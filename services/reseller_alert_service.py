from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models.reseller_alert import ResellerAlert, AlertSeverity, AlertStatus
from datetime import datetime, timedelta, timezone
from typing import List, Optional

class ResellerAlertService:
    def __init__(self, db: Session):
        self.db = db

    async def create_or_update_alert(
        self, 
        reseller_id: str, 
        sub_user_id: str, 
        sub_user_name: str, 
        plan_name: str, 
        required_credits: float, 
        available_credits: float
    ):
        """
        Creates a new alert or updates an existing one if it's within the grouping window.
        """
        shortage = required_credits - available_credits
        severity = self._calculate_severity(shortage)
        
        # Look for an unresolved alert for the same sub-user and plan within the last 30 mins
        window_start = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        existing_alert = self.db.query(ResellerAlert).filter(
            ResellerAlert.reseller_id == reseller_id,
            ResellerAlert.sub_user_id == sub_user_id,
            ResellerAlert.plan_name == plan_name,
            ResellerAlert.status == AlertStatus.UNRESOLVED,
            ResellerAlert.last_attempt_at >= window_start
        ).first()

        if existing_alert:
            # Grouping/Spam prevention: Update existing alert
            existing_alert.attempt_count += 1
            existing_alert.last_attempt_at = datetime.now(timezone.utc)
            existing_alert.available_credits = available_credits
            existing_alert.shortage = shortage
            existing_alert.severity = severity
        else:
            # Create new alert
            new_alert = ResellerAlert(
                reseller_id=reseller_id,
                sub_user_id=sub_user_id,
                sub_user_name=sub_user_name,
                plan_name=plan_name,
                required_credits=required_credits,
                available_credits=available_credits,
                shortage=shortage,
                severity=severity,
                status=AlertStatus.UNRESOLVED
            )
            self.db.add(new_alert)
        
        self.db.commit()
        
        # 🔥 NEW: Send Email Notification for NEW alerts
        if not existing_alert:
            try:
                from models.reseller import Reseller
                from services.email_service import email_service
                
                reseller = self.db.query(Reseller).filter(Reseller.reseller_id == reseller_id).first()
                if reseller and reseller.email:
                    import asyncio
                    # Send email in background to not block the main request
                    asyncio.create_task(email_service.send_credit_shortage_alert(
                        reseller_email=reseller.email,
                        sub_user_name=sub_user_name,
                        plan_name=plan_name,
                        shortage=shortage
                    ))
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error triggering alert email: {e}")

    def _calculate_severity(self, shortage: float) -> str:
        if shortage < 50:
            return AlertSeverity.LOW
        elif shortage < 200:
            return AlertSeverity.MEDIUM
        elif shortage < 500:
            return AlertSeverity.HIGH
        else:
            return AlertSeverity.CRITICAL

    def get_reseller_alerts(
        self, 
        reseller_id: str, 
        status: Optional[str] = None, 
        severity: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ):
        query = self.db.query(ResellerAlert).filter(ResellerAlert.reseller_id == reseller_id)
        
        if status:
            query = query.filter(ResellerAlert.status == status)
        if severity:
            query = query.filter(ResellerAlert.severity == severity)
            
        total = query.count()
        alerts = query.order_by(desc(ResellerAlert.last_attempt_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "alerts": [a.to_dict() for a in alerts],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def resolve_alerts_for_reseller(self, reseller_id: str, current_balance: float):
        """
        Automatically resolve alerts if the current balance is sufficient.
        """
        unresolved_alerts = self.db.query(ResellerAlert).filter(
            ResellerAlert.reseller_id == reseller_id,
            ResellerAlert.status == AlertStatus.UNRESOLVED
        ).all()
        
        resolved_count = 0
        for alert in unresolved_alerts:
            if current_balance >= alert.required_credits:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now(timezone.utc)
                resolved_count += 1
        
        if resolved_count > 0:
            self.db.commit()
        
        return resolved_count

    def get_alert_stats(self, reseller_id: str):
        """
        Fetch analytics widgets data for the reseller dashboard.
        """
        stats = self.db.query(
            ResellerAlert.status,
            func.count(ResellerAlert.id)
        ).filter(ResellerAlert.reseller_id == reseller_id).group_by(ResellerAlert.status).all()
        
        # Most active sub-users causing alerts
        top_sub_users = self.db.query(
            ResellerAlert.sub_user_name,
            func.count(ResellerAlert.id).label('count')
        ).filter(ResellerAlert.reseller_id == reseller_id).group_by(ResellerAlert.sub_user_name).order_by(desc('count')).limit(5).all()
        
        # Most requested plans causing alerts
        top_plans = self.db.query(
            ResellerAlert.plan_name,
            func.count(ResellerAlert.id).label('count')
        ).filter(ResellerAlert.reseller_id == reseller_id).group_by(ResellerAlert.plan_name).order_by(desc('count')).limit(5).all()
        
        # Total lost revenue estimation (sum of shortages for unresolved alerts)
        lost_revenue = self.db.query(func.sum(ResellerAlert.shortage)).filter(
            ResellerAlert.reseller_id == reseller_id,
            ResellerAlert.status == AlertStatus.UNRESOLVED
        ).scalar() or 0
        
        return {
            "status_counts": {s: c for s, c in stats},
            "top_sub_users": [{"name": n, "count": c} for n, c in top_sub_users],
            "top_plans": [{"name": p, "count": c} for p, c in top_plans],
            "lost_revenue_estimation": lost_revenue,
            "total_failed_attempts": self.db.query(func.sum(ResellerAlert.attempt_count)).filter(ResellerAlert.reseller_id == reseller_id).scalar() or 0
        }
