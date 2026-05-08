from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import traceback
import uuid

from models.reseller_analytics import ResellerAnalytics, BusinessUserAnalytics
from models.reseller import Reseller
from models.busi_user import BusiUser
from models.credit_distribution import CreditDistribution
from models.message_usage import MessageUsageCreditLog
from schemas.reseller_analytics import (
    ResellerDashboardResponse,
    ResellerAnalyticsCreate,
    ResellerAnalyticsUpdate,
    BusinessUserStats,
    Transaction,
    ResellerAnalytics as ResellerAnalyticsSchema
)

from models.message import Message, MessageStatus
from sqlalchemy import extract

logger = logging.getLogger(__name__)

class ResellerAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def generate_reseller_dashboard(self, reseller_id: Any) -> ResellerDashboardResponse:
        """
        Get complete reseller dashboard analytics with flat structure.
        """
        reseller_id = str(reseller_id) if reseller_id else None

        try:
            # 1. Get aggregated analytics from DB (or create headers)
            analytics = self.get_or_create_reseller_analytics(reseller_id)
            
            # 2. Get real-time business user stats
            business_stats = self.get_business_user_stats(reseller_id)
            
            # Calculate real-time total messages sent across all sub-users only
            total_messages_sent = sum(b.messages_sent for b in business_stats)
            
            # 🔥 FIX: For Reseller, 'used_credits' should be based on sub-user allocations
            reseller = self.db.query(Reseller).filter(Reseller.reseller_id == reseller_id).first()
            total_purchases = float(reseller.total_credits or 0) if reseller else 0.0
            
            # Total distributed = Sum of credits_allocated across all sub-users
            total_distributed = sum(b.credits_allocated for b in business_stats)
            
            used_credits_wallet = float(total_distributed)
            # Remaining is Total - Distributed (Ignoring any leaks)
            remaining_credits_display = max(0, total_purchases - used_credits_wallet)
            
            # Reconciliation: If the physical wallet balance is leaked, fix it
            if reseller and float(reseller.available_credits) != remaining_credits_display:
                logger.info(f"Reconciling reseller {reseller_id} wallet: {reseller.available_credits} -> {remaining_credits_display}")
                reseller.available_credits = remaining_credits_display
                reseller.used_credits = used_credits_wallet
                self.db.add(reseller)
                self.db.commit()

            # Calculate aggregate message consumption separately for reporting
            total_message_usage = sum(b.credits_used for b in business_stats)
            
            
            
            # 4. Get Recent Transactions (Credit Distributions)
            from sqlalchemy.orm import joinedload
            recent_txs_db = self.db.query(CreditDistribution).options(
                joinedload(CreditDistribution.to_business)
            ).filter(
                CreditDistribution.from_reseller_id == reseller_id
            ).order_by(desc(CreditDistribution.shared_at)).limit(10).all()
            
            recent_transactions = []
            for tx in recent_txs_db:
                b_name = tx.to_business.business_name if tx.to_business else "Unknown"
                
                recent_transactions.append(Transaction(
                    id=str(tx.distribution_id),
                    type="distribution",
                    description=f"Allocated to {b_name}",
                    amount=tx.credits_shared,
                    date=tx.shared_at or datetime.now(timezone.utc),
                    status="completed"
                ))

            # 5. [NEW] Account Info (Real)
            account_info = {
                "user_type": "Reseller", # Or reseller.role if dynamic
                "username": reseller.username if reseller else "Unknown",
                "full_name": reseller.name if reseller else "", # Added full_name
                "email": reseller.email if reseller else "",
                "reseller_id": reseller_id
            }

            # 6. [NEW] Plan Details (Mock)
            plan_details = {
                "plan_type": "MAP 8A",
                "expiry": "UNLIMITED"
            }

            # 7. [NEW] Traffic Source (Real - Aggregated by Country)
            # Aggregate business users by country
            country_stats = {}
            total_businesses = len(business_stats)
            
            # Since 'business_stats' is just a list of Pydantics, we need to query BusiUser for country
            # Optimization: Fetch country in the initial query if possible, but let's just query aggregate now
            
            traffic_db = self.db.query(
                BusiUser.country, 
                func.count(BusiUser.busi_user_id)
            ).filter(
                BusiUser.parent_reseller_id == reseller_id
            ).group_by(BusiUser.country).all()
            
            traffic_source = []
            for country, count in traffic_db:
                label = country if country else "Unknown"
                # Simple color mapping logic or handle on frontend
                traffic_source.append({
                    "name": label,
                    "value": count,
                    "percentage": round((count / max(1, total_businesses)) * 100, 1)
                })
            
            # If empty, add a placeholder or leave empty
            if not traffic_source and total_businesses > 0:
                 traffic_source.append({"name": "Unknown", "value": total_businesses, "percentage": 100})

            # 8. Update analytics if needed and construct response
            if analytics.id is not None:
                self._update_reseller_aggregates(analytics)
                # Refresh to get updated values
                self.db.refresh(analytics)
            
            return ResellerDashboardResponse(
                reseller_id=str(reseller_id),
                total_credits=int(total_purchases),
                used_credits=int(used_credits_wallet),
                remaining_credits=int(remaining_credits_display),
                wallet_balance=float(remaining_credits_display),
                messages_sent=int(total_messages_sent),
                business_users=business_stats,
                recent_transactions=recent_transactions,
                plan_details=plan_details,
                account_info=account_info,
                traffic_source=traffic_source,
                graph_data=self.get_reseller_graph_data(reseller_id),
                last_updated=analytics.updated_at or datetime.now(timezone.utc)
            )
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error in generate_reseller_dashboard: {e}")
            raise e

    def get_reseller_graph_data(self, reseller_id: Any) -> List[dict]:
        """
        [AGGREGATE GRAPH] Aggregates all messages from all business users 
        belonging to this reseller, grouped by month for the current year.
        Source: MessageUsageCreditLog for highest accuracy.
        """
        current_year = datetime.now().year
        
        try:
            # 🔥 Real-time aggregation across all sub-users + Reseller self
            sub_user_ids = self.db.query(BusiUser.busi_user_id).filter(
                BusiUser.parent_reseller_id == reseller_id
            ).all()
            all_involved_ids = [str(uid[0]) for uid in sub_user_ids]
            
            # Query MessageUsageCreditLog for all involved IDs
            stats = self.db.query(
                extract('month', MessageUsageCreditLog.timestamp).label('month'),
                func.count(MessageUsageCreditLog.usage_id).label('total')
            ).filter(
                MessageUsageCreditLog.busi_user_id.in_(all_involved_ids),
                MessageUsageCreditLog.credits_deducted > 0, # Only count actual message deductions
                MessageUsageCreditLog.source != "distribution", # Exclude transfers
                extract('year', MessageUsageCreditLog.timestamp) == current_year
            ).group_by(text('month')).order_by(text('month')).all()
            
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            result = []
            stats_dict = {int(s.month): s for s in stats}
            
            for i in range(1, 13):
                month_stat = stats_dict.get(i)
                result.append({
                    "name": month_names[i-1],
                    "sent": month_stat.total if month_stat else 0,
                    "delivered": 0 # User requested to remove delivery line, keeping key for contract compatibility
                })
            return result
        except Exception as e:
            logger.error(f"Error in get_reseller_graph_data: {e}")
            return []

    def get_business_user_stats(self, reseller_id: str) -> List[BusinessUserStats]:
        """Get statistics for all business users under a reseller in real-time."""
        businesses = self.db.query(BusiUser).filter(
            BusiUser.parent_reseller_id == reseller_id
        ).all()
        
        result = []
        for busi in businesses:
            # Calculate real-time stats
            credits_allocated = float(busi.credits_allocated or 0)
            
            credits_used = self.db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == busi.busi_user_id,
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).scalar() or 0
            
            messages_sent = self.db.query(MessageUsageCreditLog).filter(
                MessageUsageCreditLog.busi_user_id == busi.busi_user_id,
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).count()
            
            result.append(BusinessUserStats(
                user_id=str(busi.busi_user_id),
                business_name=busi.business_name or "Unknown",
                credits_allocated=float(credits_allocated),
                credits_used=float(credits_used),
                credits_remaining=float(max(0, credits_allocated - credits_used)),
                messages_sent=int(messages_sent)
            ))
        return result

    def get_top_performing_businesses(self, reseller_id: str, limit: int = 5) -> List[BusinessUserStats]:
        """Get top performing businesses based on messages sent."""
        stats = self.get_business_user_stats(reseller_id)
        # Sort by messages sent descending
        stats.sort(key=lambda x: x.messages_sent, reverse=True)
        return stats[:limit]

    def get_reseller_analytics_history(self, reseller_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical analytics snapshots."""
        history = self.db.query(ResellerAnalytics).filter(
            ResellerAnalytics.reseller_id == reseller_id
        ).order_by(desc(ResellerAnalytics.updated_at)).limit(limit).all()
        
        return [
            {
                "id": str(h.id),
                "total_credits_purchased": h.total_credits_purchased,
                "total_credits_distributed": h.total_credits_distributed,
                "total_credits_used": h.total_credits_used,
                "remaining_credits": h.remaining_credits,
                "timestamp": h.updated_at
            }
            for h in history
        ]

    def update_reseller_analytics(self, reseller_id: str, data: Any) -> Optional[Dict[str, Any]]:
        """Manually update reseller analytics fields."""
        analytics = self.db.query(ResellerAnalytics).filter(
            ResellerAnalytics.reseller_id == reseller_id
        ).first()
        
        if not analytics:
            return None
            
        if hasattr(data, 'total_credits_purchased') and data.total_credits_purchased is not None:
            analytics.total_credits_purchased = data.total_credits_purchased
        if hasattr(data, 'total_credits_distributed') and data.total_credits_distributed is not None:
            analytics.total_credits_distributed = data.total_credits_distributed
            
        analytics.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(analytics)
        
        return {
            "total_credits_purchased": analytics.total_credits_purchased,
            "total_credits_distributed": analytics.total_credits_distributed,
            "updated_at": analytics.updated_at
        }

    def get_or_create_reseller_analytics(self, reseller_id: Any) -> ResellerAnalytics:
        """Get existing analytics or create new one for reseller."""
        reseller_id = str(reseller_id) if reseller_id else None
        try:
            analytics = self.db.query(ResellerAnalytics).filter(
                ResellerAnalytics.reseller_id == reseller_id
            ).first()
            
            if not analytics:
                reseller_exists = self.db.query(Reseller.reseller_id).filter(Reseller.reseller_id == reseller_id).scalar()
                
                if not reseller_exists:
                    logger.warning(f"Reseller {reseller_id} not found when creating analytics.")
                    # Return safe dummy
                    return ResellerAnalytics(
                        reseller_id=reseller_id, 
                        total_credits_purchased=0,
                        total_credits_distributed=0,
                        total_credits_used=0,
                        remaining_credits=0,
                        business_user_stats=[],
                        updated_at=datetime.now(timezone.utc)
                    )

                analytics = ResellerAnalytics(
                    reseller_id=reseller_id,
                    total_credits_purchased=0,
                    total_credits_distributed=0,
                    total_credits_used=0,
                    remaining_credits=0,
                    business_user_stats=[],
                    updated_at=datetime.now(timezone.utc)
                )
                self.db.add(analytics)
                self.db.commit()
                self.db.refresh(analytics)
                self._update_reseller_aggregates(analytics)
            
            return analytics
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in get_or_create_reseller_analytics: {e}")
            # Fallback
            return ResellerAnalytics(
                reseller_id=reseller_id,
                total_credits_purchased=0,
                total_credits_distributed=0,
                total_credits_used=0,
                remaining_credits=0,
                business_user_stats=[],
                updated_at=datetime.now(timezone.utc)
            )

    def regenerate_all_analytics(self, reseller_id: Any) -> ResellerDashboardResponse:
        """Force recalculate ALL analytics."""
        reseller_id = str(reseller_id) if reseller_id else None
        logger.info(f"Regenerating analytics for reseller {reseller_id}")
        
        try:
            businesses = self.db.query(BusiUser).filter(
                BusiUser.parent_reseller_id == reseller_id
            ).all()
            
            for business in businesses:
                self.recalculate_business_analytics(str(business.busi_user_id), str(reseller_id))
                
            analytics = self.get_or_create_reseller_analytics(reseller_id)
            if analytics.id is not None:
                self._update_reseller_aggregates(analytics)
            
            return self.generate_reseller_dashboard(reseller_id)
        except Exception as e:
            logger.error(f"Error regenerating analytics: {e}")
            raise e

    def recalculate_business_analytics(self, business_user_id: str, reseller_id: str) -> Optional[BusinessUserAnalytics]:
        try:
            analytics = self.db.query(BusinessUserAnalytics).filter(
                BusinessUserAnalytics.business_user_id == business_user_id
            ).first()

            business_user = self.db.query(BusiUser).filter(BusiUser.busi_user_id == business_user_id).first()
            if not business_user:
                return None

            business_name = getattr(business_user, 'business_name', 'Unknown Business')

            if not analytics:
                analytics = BusinessUserAnalytics(
                    reseller_id=reseller_id,
                    business_user_id=business_user_id,
                    business_name=business_name
                )
                self.db.add(analytics)
            
            # 🔥 FIX: Calculate credits in real-time from single source of truth
            credits_allocated = self.db.query(func.sum(CreditDistribution.credits_shared)).filter(
                CreditDistribution.from_reseller_id == reseller_id,
                CreditDistribution.to_business_user_id == business_user_id
            ).scalar() or 0
            
            credits_used = self.db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id == business_user_id,
                MessageUsageCreditLog.credits_deducted > 0  # Only sum positive values (actual deductions)
            ).scalar() or 0
            
            messages_sent = self.db.query(MessageUsageCreditLog).filter(
                MessageUsageCreditLog.busi_user_id == business_user_id,
                MessageUsageCreditLog.credits_deducted > 0 # Only count messages, not distributions
            ).count()
            
            # 🔥 FIX: For business user analytics, calculate their individual remaining credits in real-time
            remaining_credits = max(0, credits_allocated - credits_used)
            
            analytics.business_name = business_name 
            analytics.credits_allocated = credits_allocated
            analytics.credits_used = credits_used
            analytics.credits_remaining = remaining_credits  # Use business user's individual remaining credits
            analytics.messages_sent = messages_sent
            analytics.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(analytics)
            return analytics
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recalculating business analytics: {e}")
            return None

    def _update_reseller_aggregates(self, analytics: ResellerAnalytics) -> ResellerAnalytics:
        try:
            reseller_id = str(analytics.reseller_id)
            
            # 🔥 Real-time aggregation across all sub-users
            sub_user_ids = self.db.query(BusiUser.busi_user_id).filter(
                BusiUser.parent_reseller_id == reseller_id
            ).all()
            sub_user_ids = [str(uid[0]) for uid in sub_user_ids]
            
            # Total used = (All sub-users) + (Reseller self)
            all_involved_ids = sub_user_ids + [reseller_id]
            
            total_used = self.db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
                MessageUsageCreditLog.busi_user_id.in_(all_involved_ids),
                MessageUsageCreditLog.credits_deducted > 0,
                MessageUsageCreditLog.source != "distribution"
            ).scalar() or 0
            
            total_distributed = self.db.query(func.sum(CreditDistribution.credits_shared)).filter(
                CreditDistribution.from_reseller_id == reseller_id
            ).scalar() or 0
            
            # Get reseller actual data
            reseller = self.db.query(Reseller).filter(Reseller.reseller_id == reseller_id).first()
            if not reseller:
                logger.warning(f"Reseller {reseller_id} not found when updating aggregates")
                return analytics
                
            total_credits_purchased = float(reseller.total_credits or 0)
            remaining_credits = float(reseller.available_credits or 0)
            
            # Sync to analytics table
            analytics.total_credits_purchased = int(total_credits_purchased)
            analytics.total_credits_distributed = int(total_distributed)
            analytics.total_credits_used = int(total_used) # This tracks message usage in history
            analytics.remaining_credits = int(remaining_credits)
            analytics.updated_at = datetime.now(timezone.utc)
            
            # 🔥 FIX: Do NOT overwrite reseller.used_credits with message usage.
            # reseller.used_credits should stay as managed by the credit purchase/distribution API.
            # This ensures (Total - Used = Available) logic holds true in the wallet.
            # 🔥 FIX: Sync reseller wallet with distribution history
            reseller.available_credits = float(remaining_credits)
            reseller.used_credits = float(total_distributed)
            self.db.add(reseller)

            self.db.commit()
            self.db.refresh(analytics)
            return analytics
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating reseller aggregates: {e}")
            raise e
