#!/usr/bin/env python3
"""
🔥 META WHATSAPP TOKEN VALIDATION API

Provides endpoints for:
- Token validation
- Token status checking
- Token updates
- Token expiry alerts
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from db.session import get_db
from api.busi_user import get_current_busi_user_id
from models.busi_user import BusiUser
from services.token_service import TokenService, get_token_service

# Response models for proper FastAPI validation
class TokenStatusResponse(BaseModel):
    has_config: bool
    config_id: Optional[int] = None
    business_number: Optional[str] = None
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    token_validation: Optional[Dict[str, Any]] = None
    recommendations: Optional[list] = None
    message: Optional[str] = None

class TokenValidationResponse(BaseModel):
    valid: bool
    status: str
    phone_number: Optional[str] = None
    verified_name: Optional[str] = None
    name_status: Optional[str] = None
    quality_rating: Optional[str] = None
    error_code: Optional[int] = None
    error_subcode: Optional[int] = None
    error_message: Optional[str] = None
    message: str

class TokenUpdateResponse(BaseModel):
    success: bool
    message: str
    validation: Optional[Dict[str, Any]] = None

class AllTokensResponse(BaseModel):
    total_configs: int
    valid_tokens: int
    expired_tokens: int
    invalid_tokens: int
    error_tokens: int
    user_details: list

router = APIRouter(prefix="/token-validation", tags=["Token Validation"])
logger = logging.getLogger(__name__)

def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_busi_user_id)
) -> BusiUser:
    user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/status", response_model=None)
async def get_token_status(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current token status and validation
    """
    try:
        token_service = TokenService(db)
        status = token_service.get_token_status_summary(str(current_user.busi_user_id))
        return status
    except Exception as e:
        logger.error(f"Error getting token status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get token status")

@router.post("/validate", response_model=None)
async def validate_token(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate current token
    """
    try:
        from models.official_whatsapp_config import OfficialWhatsAppConfig
        
        token_service = TokenService(db)
        config = token_service.db.query(OfficialWhatsAppConfig).filter(
            OfficialWhatsAppConfig.busi_user_id == str(current_user.busi_user_id)
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="No WhatsApp configuration found")
        
        validation = token_service.validate_token(config)
        return validation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate token")

@router.post("/update", response_model=None)
async def update_token(
    new_token: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update access token (validates before saving)
    """
    try:
        token_service = TokenService(db)
        result = token_service.update_token(str(current_user.busi_user_id), new_token)
        return result
    except Exception as e:
        logger.error(f"Error updating token: {e}")
        raise HTTPException(status_code=500, detail="Failed to update token")

@router.get("/admin/all-tokens", response_model=None)
async def get_all_tokens_status(
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Check all user tokens
    """
    try:
        token_service = TokenService(db)
        # Add admin check here if needed
        all_tokens = token_service.check_all_user_tokens()
        return all_tokens
    except Exception as e:
        logger.error(f"Error checking all tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to check all tokens")

@router.get("/health")
async def token_health_check():
    """
    Health check for token service
    """
    return {
        "status": "healthy",
        "service": "token_validation",
        "message": "Token validation service is running"
    }
