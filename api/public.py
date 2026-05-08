from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from db.session import get_db
from models.reseller import Reseller
from pydantic import BaseModel

router = APIRouter(tags=["Public"])

class PublicResellerResponse(BaseModel):
    reseller_id: uuid.UUID
    business_name: Optional[str]
    name: str

@router.get("/reseller/{reseller_id}", response_model=PublicResellerResponse)
async def get_public_reseller_info(reseller_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get non-sensitive reseller info for registration pages."""
    reseller = db.query(Reseller).filter(Reseller.reseller_id == reseller_id).first()
    if not reseller:
        raise HTTPException(status_code=404, detail="Reseller not found")
    
    return PublicResellerResponse(
        reseller_id=reseller.reseller_id,
        business_name=reseller.business_name,
        name=reseller.name
    )
