from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from db.session import get_db
from services.reseller_service import ResellerService
from schemas.reseller import (
    ResellerCreateSchema, 
    ResellerUpdateSchema, 
    ResellerResponseSchema, 
    ResellerLoginSchema,
    ResellerResponseWithTokenSchema,
    ResellerLogoutResponseSchema,
    ProfileResponseSchema,
    BusinessSchema,
    AddressSchema,
    BankSchema,
    WalletSchema
)
from schemas.busi_user import PlanResponseSchema
from models.plan import Plan
from core.security import create_access_token, verify_token, verify_password, create_refresh_token
from datetime import timedelta

router = APIRouter(tags=["Resellers"])


# Dependency for getting current reseller token
async def get_current_reseller_token(authorization: str = Header(None)):
    """Extract token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )
    
    return authorization.split(" ")[1]


from core.rate_limiter import registration_rate_limiter

@router.post("/register", response_model=ResellerResponseWithTokenSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(registration_rate_limiter)])
async def register_reseller(reseller_data: ResellerCreateSchema, request: Request, db: Session = Depends(get_db)):
    """Register a new reseller."""
    reseller_service = ResellerService(db)
    
    try:
        reseller = reseller_service.create_reseller(reseller_data, request=request)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(reseller.reseller_id), "email": reseller.email, "role": reseller.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(reseller.reseller_id), "email": reseller.email, "role": reseller.role}
        )
        
        return ResellerResponseWithTokenSchema(
            reseller=ResellerResponseSchema.model_validate(reseller),
            access_token=access_token,
            refresh_token=refresh_token
        )
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
        import traceback
        print(f"Error in register_reseller: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reseller: {str(e)}"
        )


@router.post("/login", response_model=ResellerResponseWithTokenSchema)
async def login_reseller(login_data: ResellerLoginSchema, db: Session = Depends(get_db)):
    """Authenticate reseller and return access token."""
    reseller_service = ResellerService(db)
    
    from services.email_validator import normalize_email
    try:
        email = normalize_email(login_data.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    reseller = reseller_service.get_reseller_by_email(email)
    
    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="USER_NOT_FOUND"
        )
    
    # Robust Password Verification
    password_valid = False
    password_migrated = False

    # 1. Try standard Bcrypt verification
    if verify_password(login_data.password, reseller.password_hash):
        password_valid = True
    
    # 2. If failed, check for legacy PLAIN TEXT password
    # Only if the stored hash doesn't look like a valid bcrypt hash (optional safety) 
    # OR just check equality if verify fails.
    elif reseller.password_hash == login_data.password.strip():
         print(f"DEBUG: Found plain text password for reseller {email}. Migrating...")
         password_valid = True
         # Migrate to Bcrypt
         from core.security import get_password_hash
         reseller.password_hash = get_password_hash(login_data.password.strip())
         password_migrated = True

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_PASSWORD"
        )
    
    if password_migrated:
        try:
            db.commit()
            db.refresh(reseller)
            print(f"DEBUG: Password migrated successfully for {email}")
        except Exception as e:
            print(f"ERROR: Failed to migrate password for {email}: {e}")
            # We don't block login if migration fails, but it's bad.
            # Continue allowing login.

    if reseller.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    try:
        # Create access token
        access_token = create_access_token(
            data={"sub": str(reseller.reseller_id), "email": reseller.email, "role": reseller.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(reseller.reseller_id), "email": reseller.email, "role": reseller.role}
        )
        
        return ResellerResponseWithTokenSchema(
            reseller=ResellerResponseSchema(
                reseller_id=reseller.reseller_id,
                role=reseller.role,
                status=reseller.status,
                created_at=reseller.created_at,
                updated_at=reseller.updated_at,
                profile=ProfileResponseSchema(
                    name=reseller.name,
                    username=reseller.username,
                    email=reseller.email,
                    phone=reseller.phone,
                    profile_image=reseller.profile_image
                ),
                business=BusinessSchema(
                    business_name=reseller.business_name,
                    organization_type=reseller.organization_type,
                    business_description=reseller.business_description,
                    erp_system=reseller.erp_system,
                    gstin=reseller.gstin if reseller.gstin else None
                ) if reseller.business_name is not None else None,
                address=AddressSchema(
                    full_address=reseller.full_address,
                    pincode=reseller.pincode,
                    country=reseller.country
                ) if reseller.full_address is not None else None,
                bank=BankSchema(
                    bank_name=reseller.bank_name
                ) if reseller.bank_name is not None else None,
                wallet=WalletSchema(
                    total_credits=reseller.total_credits,
                    available_credits=reseller.available_credits,
                    used_credits=reseller.used_credits
                )
            ),
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/logout", response_model=ResellerLogoutResponseSchema)
async def logout_reseller():
    """Logout reseller (client-side token removal)."""
    return ResellerLogoutResponseSchema(
        message="Successfully logged out",
        detail="Please remove the token from client storage"
    )


@router.get("/me", response_model=ResellerResponseSchema)
async def get_current_reseller(
    token: str = Depends(get_current_reseller_token),
    db: Session = Depends(get_db)
):
    """Get current reseller profile."""
    reseller_service = ResellerService(db)
    
    payload = verify_token(token)
    if not payload or "error" in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    if payload.get("type", "access") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )
    
    # Check if token belongs to a reseller
    role = payload.get("role", "").lower()
    if role not in ["reseller", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Reseller only (role: {role})"
        )
    
    reseller_id = payload.get("sub")
    reseller = reseller_service.get_reseller_by_id(reseller_id)
    
    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseller not found"
        )
    
    # Manual mapping to ensure nested objects (business, address, bank) are populated
    # since these aren't unified objects in the SQLAlchemy Reseller model.
    return ResellerResponseSchema(
        reseller_id=reseller.reseller_id,
        role=reseller.role,
        status=reseller.status,
        created_at=reseller.created_at,
        updated_at=reseller.updated_at,
        profile=ProfileResponseSchema(
            name=reseller.name,
            username=reseller.username,
            email=reseller.email,
            phone=reseller.phone,
            profile_image=reseller.profile_image
        ),
        business=BusinessSchema(
            business_name=reseller.business_name,
            organization_type=reseller.organization_type,
            business_description=reseller.business_description,
            erp_system=reseller.erp_system,
            gstin=reseller.gstin if reseller.gstin else None
        ) if reseller.business_name is not None else None,
        address=AddressSchema(
            full_address=reseller.full_address,
            pincode=reseller.pincode,
            country=reseller.country
        ) if reseller.full_address is not None else None,
        bank=BankSchema(
            bank_name=reseller.bank_name
        ) if reseller.bank_name is not None else None,
        wallet=WalletSchema(
            total_credits=reseller.total_credits or 0.0,
            available_credits=reseller.available_credits or 0.0,
            used_credits=reseller.used_credits or 0.0
        ),
        plan_name=reseller.plan_name,
        plan_expiry=reseller.plan_expiry
    )


@router.put("/me", response_model=ResellerResponseSchema)
async def update_current_reseller(
    reseller_data: ResellerUpdateSchema,
    token: str = Depends(get_current_reseller_token),
    db: Session = Depends(get_db)
):
    """Update current reseller profile."""
    reseller_service = ResellerService(db)
    
    payload = verify_token(token)
    if not payload or "error" in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    if payload.get("type", "access") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )
    
    reseller_id = payload.get("sub")
    
    try:
        reseller = reseller_service.update_reseller(reseller_id, reseller_data)
        return ResellerResponseSchema.model_validate(reseller)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reseller"
        )


@router.get("/", response_model=List[ResellerResponseSchema])
async def get_resellers(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(get_current_reseller_token),
    db: Session = Depends(get_db)
):
    """Get list of resellers (admin only)."""
    payload = verify_token(token)
    if not payload or "error" in payload or payload.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    if payload.get("type", "access") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )
    
    reseller_service = ResellerService(db)
    resellers = reseller_service.get_resellers(skip=skip, limit=limit)
    
    return [ResellerResponseSchema.model_validate(reseller) for reseller in resellers]


@router.get("/{reseller_id}", response_model=ResellerResponseSchema)
async def get_reseller(
    reseller_id: str,
    token: str = Depends(get_current_reseller_token),
    db: Session = Depends(get_db)
):
    """Get reseller by ID (admin or own reseller)."""
    payload = verify_token(token)
    if not payload or "error" in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    if payload.get("type", "access") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )
    
    current_reseller_id = payload.get("sub")
    current_role = payload.get("role")
    
    # Resellers can only view their own profile unless they're admin
    if current_reseller_id != reseller_id and current_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    reseller_service = ResellerService(db)
    reseller = reseller_service.get_reseller_by_id(reseller_id)
    
    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseller not found"
        )
    
    return ResellerResponseSchema.model_validate(reseller)


@router.get("/plans/available", response_model=List[PlanResponseSchema])
async def get_available_reseller_plans(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all available plans for resellers (optionally filter by category)."""
    query = db.query(Plan).filter(Plan.status == "active")
    
    if category:
        query = query.filter(Plan.plan_category == category.upper())
    else:
        # Default to RESELLER plans if no category specified
        query = query.filter(Plan.plan_category == "RESELLER")
        
    return query.all()
