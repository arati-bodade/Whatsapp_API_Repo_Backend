from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import uuid

from db.session import get_db
from api.auth import get_current_user
from services.busi_user_service import BusiUserService
from schemas.busi_user import (
    BusiUserProfileSchema,
    BusiUserProfileResponseSchema,
    BusiUserInfoSchema,
    BusiUserAddressSchema,
    BusiUserWalletSchema,
    BusiUserCreateSchema,
    BusiUserUpdateSchema,
    BusiUserResponseSchema,
    BusiUserLoginSchema,
    BusiUserResponseWithTokenSchema,
    BusiUserLogoutResponseSchema,
    BusiUserAnalyticsSchema,
    PlanResponseSchema,
)
from models.plan import Plan
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.admin import MasterAdmin
from core.security import create_access_token, verify_token, create_refresh_token
from core.plan_validator import check_reseller_plan
from datetime import timedelta
import logging
from api.me import get_my_plan as get_standardized_plan # 🔥 Restoration alias


logger = logging.getLogger(__name__)

def map_busi_user_to_response(busi_user, db: Session = None) -> BusiUserResponseSchema:
    """Helper to map BusiUser ORM model to BusiUserResponseSchema with real-time credit calculation."""
    try:
        connection_status = "disconnected"
        if db:
            from models.device import Device, SessionStatus
            is_connected = db.query(Device).filter(
                Device.busi_user_id == str(busi_user.busi_user_id),
                Device.session_status == SessionStatus.connected,
                Device.is_active == True
            ).first() is not None
            connection_status = "connected" if is_connected else "disconnected"

        # 🔥 REAL-TIME CREDIT CALCULATION
        # Table values for allocated credits are the authority (handles distributions + direct purchases)
        credits_allocated = max(0, busi_user.credits_allocated or 0)
        
        # Real-time used credits from logs
        from models.message_usage import MessageUsageCreditLog
        credits_used = db.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
            MessageUsageCreditLog.busi_user_id == str(busi_user.busi_user_id),
            MessageUsageCreditLog.credits_deducted > 0
        ).scalar() or 0
        
        # Remaining is calculated live
        credits_remaining = max(0, credits_allocated - credits_used)

        response_data = {
            "busi_user_id": busi_user.busi_user_id,
            "role": busi_user.role or "business_owner",
            "status": busi_user.status or "active",
            "parent_reseller_id": busi_user.parent_reseller_id,
            "created_at": busi_user.created_at,
            "updated_at": busi_user.updated_at,
            "profile": {
                "name": busi_user.name or "",
                "username": busi_user.username or "",
                "email": busi_user.email or "",
                "phone": busi_user.phone or "",
                "profile_image": busi_user.profile_image
            },
            "business": {
                "business_name": busi_user.business_name or "Unknown",
                "organization_type": getattr(busi_user, 'organization_type', None),
                "business_description": busi_user.business_description,
                "erp_system": busi_user.erp_system,
                "gstin": busi_user.gstin if busi_user.gstin else None,
                "bank_name": getattr(busi_user, 'bank_name', None)
            },
            "address": {
                "full_address": busi_user.full_address,
                "pincode": busi_user.pincode,
                "country": busi_user.country
            } if busi_user.full_address else None,
            "wallet": {
                "credits_allocated": credits_allocated,
                "credits_used": credits_used,
                "credits_remaining": credits_remaining
            },
            "whatsapp_mode": busi_user.whatsapp_mode or "unofficial",
            "plan_name": getattr(busi_user, 'plan_name', None),
            "plan_expiry": getattr(busi_user, 'plan_expiry', None),
            "connection_status": connection_status
        }
        return BusiUserResponseSchema(**response_data)
    except Exception as e:
        logger.error(f"Error mapping busi_user {getattr(busi_user, 'busi_user_id', 'unknown')}: {e}")
        raise e

router = APIRouter(tags=["busi_users"])


def get_busi_user_service(db: Session = Depends(get_db)) -> BusiUserService:
    return BusiUserService(db)


async def get_current_busi_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    
    # Debug: Log full payload
    logger.warning(f"[BUSI_USER_AUTH] Full token payload: {payload}")
    
    if not payload or payload.get("error"):
        error_type = payload.get("error", "invalid_token") if payload else "invalid_token"
        error_message = payload.get("message", "Invalid or expired token") if payload else "Invalid or expired token"
        
        if error_type == "token_expired":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please log in again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )
            
    if payload.get("type", "access") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )

    # Check for business user roles (Admins allowed for management/debugging)
    role = (payload.get("role") or "").lower()
    # Allow all business user roles plus admin roles for debugging
    allowed_roles = ["user", "business_owner", "business", "admin", "super_admin", "customer", "client", "business_user", "busi_user", "owner"]
    
    # Debug logging to see what role is being rejected
    logger.warning(f"[BUSI_USER_AUTH] Checking role: '{role}' (original: '{payload.get('role')}')")
    logger.warning(f"[BUSI_USER_AUTH] Allowed roles: {allowed_roles}")
    
    if role not in allowed_roles:
         logger.error(f"[BUSI_USER_AUTH] Role '{role}' not in allowed roles")
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Business User or Admin only (role: {role})"
        )
    return str(payload.get("sub"))


async def get_current_reseller_token_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload or payload.get("error"):
        error_type = payload.get("error", "invalid_token") if payload else "invalid_token"
        error_message = payload.get("message", "Invalid or expired token") if payload else "Invalid or expired token"
        
        if error_type == "token_expired":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please log in again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )
            
    if payload.get("type", "access") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )

    # Check if role is reseller or admin
    role = (payload.get("role") or "").lower()
    if role not in ["reseller", "admin", "super_admin"]:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Reseller only (role: {role})"
        )
    return str(payload.get("sub"))


@router.get("/my-users", response_model=List[BusiUserResponseSchema])
async def get_my_busi_users(
    skip: int = 0,
    limit: int = 100,
    reseller_id: str = Depends(get_current_reseller_token_id),
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Get all business users belonging to the currently logged-in reseller."""
    busi_useres = busi_user_service.get_busi_useres_by_reseller(reseller_id, skip=skip, limit=limit)
    return [map_busi_user_to_response(bu, db=busi_user_service.db) for bu in busi_useres]


@router.get("/me", response_model=BusiUserResponseSchema)
async def get_current_busi_user(
    busi_user_id: str = Depends(get_current_busi_user_id),
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Get the profile of the currently logged-in business user."""
    busi_user = busi_user_service.get_busi_user_by_id(busi_user_id)
    if not busi_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BusiUser not found"
        )
    return map_busi_user_to_response(busi_user, db=busi_user_service.db)


@router.put("/me", response_model=BusiUserResponseSchema)
async def update_my_profile(
    busi_user_data: BusiUserUpdateSchema,
    busi_user_id: str = Depends(get_current_busi_user_id),
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Update the profile of the currently logged-in business user."""
    try:
        busi_user = busi_user_service.update_busi_user(busi_user_id, busi_user_data)
        if not busi_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BusiUser not found"
            )
        return map_busi_user_to_response(busi_user, db=busi_user_service.db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/analytics", response_model=BusiUserAnalyticsSchema)
async def get_busi_user_analytics(
    reseller_id: str = Depends(get_current_reseller_token_id),
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Get analytics for the logged-in reseller's business users."""
    stats = busi_user_service.get_reseller_analytics(reseller_id)
    return BusiUserAnalyticsSchema(**stats)


from core.rate_limiter import registration_rate_limiter

@router.post("/register", response_model=BusiUserResponseSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(registration_rate_limiter)])
async def register_busi_user(
    busi_user_data: BusiUserCreateSchema,
    request: Request,
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Register a new busi_user user."""
    # NEW: Check if the reseller in the data is actually a reseller and what is their plan status
    # This assumes signups are done by resellers. If it's a public signup, logic might differ.
    if busi_user_data.parent_reseller_id:
        check_reseller_plan(busi_user_service.db, str(busi_user_data.parent_reseller_id))
    
    try:
        created_by = None
        if busi_user_data.parent_reseller_id:
            created_by = busi_user_data.parent_reseller_id
        
        busi_user = busi_user_service.create_busi_user(busi_user_data, created_by=created_by, request=request)
        
        return map_busi_user_to_response(busi_user, db=busi_user_service.db)
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "EMAIL_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="EMAIL_ALREADY_EXISTS"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating busi_user: {str(e)}"
        )


@router.post("/login", response_model=BusiUserResponseWithTokenSchema)
async def login_busi_user(
    login_data: BusiUserLoginSchema,
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    from services.email_validator import normalize_email
    try:
        email = normalize_email(login_data.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    # 1. Check if user exists
    busi_user = busi_user_service.get_business_by_email(email)
    if not busi_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="USER_NOT_FOUND",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Authenticate
    authenticated_user = busi_user_service.authenticate_busi_user(email, login_data.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_PASSWORD",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    busi_user = authenticated_user
    
    if busi_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )

    access_token = create_access_token(
        data={"sub": str(busi_user.busi_user_id), "email": busi_user.email, "role": busi_user.role}
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(busi_user.busi_user_id), "email": busi_user.email, "role": busi_user.role}
    )

    return BusiUserResponseWithTokenSchema(
        busi_user=map_busi_user_to_response(busi_user, db=busi_user_service.db),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/", response_model=List[BusiUserResponseSchema])
async def get_busi_useres(
    skip: int = 0,
    limit: int = 100,
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Get all busi_useres with pagination."""
    busi_useres = busi_user_service.get_all_busi_useres(skip=skip, limit=limit)
    return [map_busi_user_to_response(bu, db=busi_user_service.db) for bu in busi_useres]


@router.get("/reseller/{reseller_id}", response_model=List[BusiUserResponseSchema])
async def get_busi_useres_by_reseller(
    reseller_id: str,
    skip: int = 0,
    limit: int = 100,
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Get all busi_useres under a specific reseller."""
    busi_useres = busi_user_service.get_busi_useres_by_reseller(reseller_id, skip=skip, limit=limit)
    return [map_busi_user_to_response(bu, db=busi_user_service.db) for bu in busi_useres]


@router.post("/logout", response_model=BusiUserLogoutResponseSchema)
async def logout_busi_user():
    """Logout busi_user user."""
    return BusiUserLogoutResponseSchema(
        message="BusiUser successfully logged out",
        detail="BusiUser session terminated, please discard your access token"
    )


@router.get("/plans/available", response_model=List[PlanResponseSchema])
async def get_available_plans(
    db: Session = Depends(get_db)
):
    """Get all available plans for business users."""
    plans = db.query(Plan).filter(Plan.plan_category == "BUSINESS", Plan.status == "active").all()
    return plans


@router.get("/me/plan", response_model=dict)
async def get_my_plan_legacy(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restored legacy route for frontend compatibility. 
    Redirects to the standardized plan retrieval logic.
    """
    return await get_standardized_plan(current_user, db)





@router.get("/{busi_user_id}", response_model=BusiUserResponseSchema)
async def get_busi_user(
    busi_user_id: str,
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Get a specific busi_user by ID."""
    busi_user = busi_user_service.get_busi_user_by_id(busi_user_id)
    if not busi_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BusiUser not found"
        )
    
    return map_busi_user_to_response(busi_user, db=busi_user_service.db)


@router.put("/{busi_user_id}", response_model=BusiUserResponseSchema)
async def update_busi_user(
    busi_user_id: str,
    busi_user_data: BusiUserUpdateSchema,
    reseller_id: str = Depends(get_current_reseller_token_id),
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Update a specific busi_user."""
    # NEW: Check Reseller Plan/Credits before updating user (e.g. allocating credits)
    check_reseller_plan(busi_user_service.db, reseller_id)

    try:
        busi_user = busi_user_service.update_busi_user(busi_user_id, busi_user_data, reseller_id)
        if not busi_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BusiUser not found"
            )
        
        return map_busi_user_to_response(busi_user, db=busi_user_service.db)
    except ValueError as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if "Unauthorized" in str(e):
             status_code = status.HTTP_403_FORBIDDEN
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )


@router.delete("/{busi_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_busi_user(
    busi_user_id: str,
    reseller_id: str = Depends(get_current_reseller_token_id),
    busi_user_service: BusiUserService = Depends(get_busi_user_service)
):
    """Delete a specific busi_user."""
    try:
        success = busi_user_service.delete_busi_user(busi_user_id, reseller_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BusiUser not found"
            )
    except ValueError as e:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )



