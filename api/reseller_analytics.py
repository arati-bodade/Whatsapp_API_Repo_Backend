from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db.session import get_db
from schemas.reseller_analytics import (
    ResellerDashboardResponse,
    ResellerAnalyticsCreate,
    ResellerAnalyticsUpdate
)
from services.reseller_analytics_service import ResellerAnalyticsService

router = APIRouter()


@router.get("/dashboard/{reseller_id}", response_model=ResellerDashboardResponse)
async def get_reseller_dashboard(
    reseller_id: str,
    db: Session = Depends(get_db)
):
    """Get complete reseller dashboard analytics."""
    service = ResellerAnalyticsService(db)
    
    try:
        dashboard = service.generate_reseller_dashboard(reseller_id)
        return dashboard
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"CRITICAL ERROR generating dashboard for {reseller_id}: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating dashboard: {str(e)}"
        )


@router.get("/business-stats/{reseller_id}")
async def get_business_user_stats(
    reseller_id: str,
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get statistics for all business users under a reseller."""
    service = ResellerAnalyticsService(db)
    
    try:
        business_stats = service.get_business_user_stats(reseller_id)
        return {
            "reseller_id": reseller_id,
            "total_businesses": len(business_stats),
            "business_stats": business_stats[:limit]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching business stats: {str(e)}"
        )


@router.get("/top-businesses/{reseller_id}")
async def get_top_performing_businesses(
    reseller_id: str,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get top performing businesses by credits used."""
    service = ResellerAnalyticsService(db)
    
    try:
        top_businesses = service.get_top_performing_businesses(reseller_id, limit)
        return {
            "reseller_id": reseller_id,
            "top_businesses": top_businesses,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching top businesses: {str(e)}"
        )


@router.get("/analytics/{reseller_id}")
async def get_reseller_analytics(
    reseller_id: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get historical analytics for a reseller."""
    service = ResellerAnalyticsService(db)
    
    try:
        analytics_history = service.get_reseller_analytics_history(reseller_id, limit)
        return {
            "reseller_id": reseller_id,
            "analytics_history": analytics_history,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching analytics history: {str(e)}"
        )


@router.post("/analytics/{reseller_id}", response_model=ResellerDashboardResponse)
async def regenerate_analytics(
    reseller_id: str,
    db: Session = Depends(get_db)
):
    """
    Force regenerate all analytics for a reseller.
    Recalculates from ground truth data and updates the database.
    """
    service = ResellerAnalyticsService(db)
    
    try:
        dashboard = service.regenerate_all_analytics(reseller_id)
        return dashboard
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerating analytics: {str(e)}"
        )


@router.put("/analytics/{reseller_id}")
async def update_analytics(
    reseller_id: str,
    analytics_data: ResellerAnalyticsUpdate,
    db: Session = Depends(get_db)
):
    """Update reseller analytics."""
    service = ResellerAnalyticsService(db)
    
    try:
        analytics = service.update_reseller_analytics(reseller_id, analytics_data)
        
        if not analytics:
            raise HTTPException(
                status_code=404,
                detail="Reseller not found"
            )
        
        return {
            "message": "Analytics updated successfully",
            "reseller_id": reseller_id,
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating analytics: {str(e)}"
        )


@router.get("/summary/{reseller_id}")
async def get_reseller_summary(
    reseller_id: str,
    db: Session = Depends(get_db)
):
    """Get quick summary of reseller performance."""
    service = ResellerAnalyticsService(db)
    
    try:
        dashboard = service.generate_reseller_dashboard(reseller_id)
        analytics = dashboard.analytics
        business_stats = dashboard.business_user_stats
        
        # Calculate additional metrics
        total_businesses = len(business_stats)
        active_businesses = len([b for b in business_stats if b.credits_used > 0])
        avg_credits_per_business = analytics.total_credits_distributed / max(1, total_businesses)
        
        return {
            "reseller_id": reseller_id,
            "quick_stats": {
                "total_businesses": total_businesses,
                "active_businesses": active_businesses,
                "total_credits_purchased": analytics.total_credits_purchased,
                "total_credits_distributed": analytics.total_credits_distributed,
                "total_credits_used": analytics.total_credits_used,
                "remaining_credits": analytics.remaining_credits,
                "avg_credits_per_business": round(avg_credits_per_business, 2),
                "usage_rate": round((analytics.total_credits_used / max(1, analytics.total_credits_distributed)) * 100, 2)
            },
            "generated_at": dashboard.generated_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )
