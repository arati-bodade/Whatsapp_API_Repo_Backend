from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from db.session import get_db
from schemas.audit_log import AuditLogResponse, AuditLogSchema
from services.audit_log_service import AuditLogService

from api.resellers import get_current_reseller_token
from core.security import verify_token

router = APIRouter()

@router.get("/me", response_model=AuditLogResponse)
async def get_my_audit_logs(
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    token: str = Depends(get_current_reseller_token),
    db: Session = Depends(get_db)
):
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if payload has error field (expired token)
        if isinstance(payload, dict) and payload.get("error"):
            if payload.get("error") == "token_expired":
                raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
        
        reseller_id = payload.get("sub")
        if not reseller_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        reseller_uuid = str(reseller_id)
        service = AuditLogService(db)
        
        logs, total, filtered = service.get_logs(
            reseller_id=reseller_uuid,
            module=module,
            action=action,
            search=search,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
                
        last_activity = service.get_last_activity_days_ago(reseller_uuid)
        
        return AuditLogResponse(
            total=total,
            filtered=filtered,
            last_activity_days_ago=last_activity,
            logs=[AuditLogSchema(**log.to_dict()) for log in logs]
        )
    except ValueError as e:
        import logging
        logger = logging.getLogger("api.audit_logs")
        logger.error(f"Invalid UUID format in token: '{reseller_id}'")
        raise HTTPException(status_code=400, detail=f"Invalid reseller_id format in token: {reseller_id}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{reseller_id}", response_model=AuditLogResponse)
async def get_audit_logs(
    reseller_id: str,
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    token: str = Depends(get_current_reseller_token),
    db: Session = Depends(get_db)
):
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if payload has error field (expired token)
        if isinstance(payload, dict) and payload.get("error"):
            if payload.get("error") == "token_expired":
                raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
        
        reseller_id = payload.get("sub")
        if not reseller_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        reseller_uuid = str(reseller_id)
        service = AuditLogService(db)
        
        logs, total, filtered = service.get_logs(
            reseller_id=reseller_uuid,
            module=module,
            action=action,
            search=search,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
                
        last_activity = service.get_last_activity_days_ago(reseller_uuid)
        
        return AuditLogResponse(
            total=total,
            filtered=filtered,
            last_activity_days_ago=last_activity,
            logs=[AuditLogSchema(**log.to_dict()) for log in logs]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reseller_id format")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
