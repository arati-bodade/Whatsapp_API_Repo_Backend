from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from db.session import get_db
from schemas.credit_distribution import (
    CreditDistributionCreateSchema,
    CreditDistributionResponseSchema,
    CreditDistributionListSchema,
    CreditDistributionSummarySchema
)
from services.credit_distribution_service import CreditDistributionService
from core.security import verify_token
import uuid

router = APIRouter(prefix="/credits", tags=["Credit Distribution"])

# Dependency for authorization (reusing reseller logic or general token verify)
async def get_current_reseller_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload or payload.get("error"):
        error_type = payload.get("error", "invalid_token") if payload else "invalid_token"
        error_message = payload.get("message", "Invalid or expired token") if payload else "Invalid or expired token"
        
        if error_type == "token_expired":
            raise HTTPException(
                status_code=401,
                detail="Token has expired. Please log in again."
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=error_message
            )
    
    # Ensure it's a reseller
    role = payload.get("role")
    if role not in ["reseller", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return str(payload.get("sub"))

async def distribute_credits(
    data: CreditDistributionCreateSchema,
    reseller_id: str = Depends(get_current_reseller_id),
    db: Session = Depends(get_db)
):
    service = CreditDistributionService(db)
    return service.distribute_credits(data, reseller_id)

@router.get("/history/reseller", response_model=List[CreditDistributionSummarySchema])
async def get_reseller_history(
    skip: int = 0,
    limit: int = 100,
    reseller_id: str = Depends(get_current_reseller_id),
    db: Session = Depends(get_db)
):
    service = CreditDistributionService(db)
    distributions = service.get_history_by_reseller(reseller_id, skip, limit)
    
    # Manual enrichment for summary view
    results = []
    for d in distributions:
        results.append({
            "distribution_id": d.distribution_id,
            "from_reseller_id": d.from_reseller_id,
            "to_business_user_id": d.to_business_user_id,
            "credits_shared": d.credits_shared,
            "shared_at": d.shared_at,
            "created_at": d.created_at,
            "from_reseller_name": d.from_reseller.name if d.from_reseller else None,
            "to_business_name": d.to_business.business_name if d.to_business else None 
        })
    return results

@router.get("/history/business/{business_id}", response_model=List[CreditDistributionSummarySchema])
async def get_business_history(
    business_id: str,
    skip: int = 0,
    limit: int = 100,
    reseller_id: str = Depends(get_current_reseller_id),
    db: Session = Depends(get_db)
):
    # For now, allowing reseller to view any business history if they are logged in.
    # We could add strict check if business belongs to reseller here.
    service = CreditDistributionService(db)
    distributions = service.get_history_by_business(business_id, skip, limit)
    
    results = []
    for d in distributions:
        results.append({
            "distribution_id": d.distribution_id,
            "from_reseller_id": d.from_reseller_id,
            "to_business_user_id": d.to_business_user_id,
            "credits_shared": d.credits_shared,
            "shared_at": d.shared_at,
            "created_at": d.created_at,
            "from_reseller_name": d.from_reseller.name if d.from_reseller else None,
            "to_business_name": d.to_business.business_name if d.to_business else None
        })
    return results
