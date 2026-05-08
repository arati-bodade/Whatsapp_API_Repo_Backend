from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from db.session import get_db
from core.security import get_current_user_id
from models.reseller import Reseller
from services.reseller_alert_service import ResellerAlertService
from pydantic import BaseModel

router = APIRouter(tags=["Reseller Alerts"])

@router.get("/")
async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get all credit shortage alerts for the logged-in reseller.
    Supports filtering by status and severity.
    """
    reseller = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
    if not reseller:
        raise HTTPException(status_code=403, detail="Only resellers can access these alerts")
        
    service = ResellerAlertService(db)
    return service.get_reseller_alerts(
        reseller_id=user_id,
        status=status,
        severity=severity,
        page=page,
        page_size=page_size
    )

@router.get("/stats")
async def get_alert_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get alert analytics for the reseller dashboard.
    """
    reseller = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
    if not reseller:
        raise HTTPException(status_code=403, detail="Only resellers can access these stats")
        
    service = ResellerAlertService(db)
    return service.get_alert_stats(user_id)

@router.post("/{alert_id}/resolve")
async def manual_resolve_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Manually mark an alert as resolved.
    """
    from models.reseller_alert import ResellerAlert, AlertStatus
    from datetime import datetime, timezone
    
    alert = db.query(ResellerAlert).filter(
        ResellerAlert.alert_id == alert_id,
        ResellerAlert.reseller_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"success": True, "message": "Alert resolved successfully"}
