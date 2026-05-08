from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import shutil
from db.session import get_db
from models.admin import MasterAdmin
from models.reseller import Reseller
from models.busi_user import BusiUser
from models.plan import Plan
from core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from api.auth import get_current_user
from pydantic import BaseModel, EmailStr
import uuid
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from models.message import Message, MessageType
from models.audit_log import AuditLog
from models.reseller_analytics import ResellerAnalytics, BusinessUserAnalytics
from models.credit_distribution import CreditDistribution
from models.message_usage import MessageUsageCreditLog
from models.official_whatsapp_config import WhatsAppTemplate, WhatsAppWebhookLog
from models.campaign import Campaign, CampaignDevice, MessageTemplate as CampaignTemplate, MessageLog
from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory
from models.device import Device, SessionStatus as DeviceSessionStatus
from models.device_session import DeviceSession
from models.whatsapp_inbox import WhatsAppInbox
from models.whatsapp_messages import WhatsAppMessages


router = APIRouter(tags=["Admin"])

# --- Schemas ---
class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PlanCreateRequest(BaseModel):
    name: str
    price: float
    credits_offered: int
    validity_days: int
    deduction_value: float
    plan_category: str # "BUSINESS" or "RESELLER"

class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    credits_offered: Optional[int] = None
    validity_days: Optional[int] = None
    deduction_value: Optional[float] = None
    plan_category: Optional[str] = None
    status: Optional[str] = None

class ResellerCreateRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: str
    password: str
    business_name: Optional[str] = None
    plan_id: Optional[str] = None

class AdminProfileUpdateRequest(BaseModel):
    name: str
    phone: str
    business_name: Optional[str] = None
    gstin: Optional[str] = None
    bio: str
    location: str

class BusiUserDirectCreateRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: str
    password: str
    business_name: str
    plan_id: str

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    business_name: Optional[str] = None
    plan_id: Optional[str] = None
    credits_allocated: Optional[float] = None

# --- Logic ---

@router.post("/login")
async def admin_login(login_data: AdminLoginRequest, db: Session = Depends(get_db)):
    # 1. Try to find admin by email or username
    admin = db.query(MasterAdmin).filter(
        (MasterAdmin.email == login_data.email) | (MasterAdmin.username == login_data.email)
    ).first()
    
    if not admin:
        raise HTTPException(status_code=401, detail="USER_NOT_FOUND")
    
    # 2. Verify password
    if not verify_password(login_data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="INVALID_PASSWORD")
    
    access_token = create_access_token(data={"sub": str(admin.admin_id), "role": "admin", "email": admin.email})
    refresh_token = create_refresh_token(data={"sub": str(admin.admin_id), "role": "admin", "email": admin.email})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer", 
        "role": "admin",
        "email": admin.email,
        "name": admin.name or admin.username
    }

@router.post("/logout")
async def admin_logout():
    return {"message": "Successfully logged out from Admin session"}

@router.get("/profile")
async def get_admin_profile(
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 Get real profile data of the logged-in administrator """
    # Verify we are indeed an admin
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
        
    admin_obj = current_admin
    
    total_campaigns = db.query(Message).filter(Message.message_type == MessageType.TEMPLATE).count()
    users_managed = db.query(BusiUser).count() + db.query(Reseller).count()
        
    formatted_date = admin_obj.created_at.strftime("%B %Y") if admin_obj.created_at else "Unknown"
        
    return {
        "name": admin_obj.name or admin_obj.username.replace("_", " ").title(),
        "username": admin_obj.username,
        "email": admin_obj.email,
        "role": "Super Admin",
        "joinedDate": formatted_date,
        "location": admin_obj.location or "Global System Server",
        "phone": admin_obj.phone or "Not Provided",
        "business_name": admin_obj.business_name or "Not Provided",
        "gstin": admin_obj.gstin or "Not Provided",
        "bio": admin_obj.bio or "Experienced system administrator specializing in large-scale WhatsApp infrastructure and automation systems.",
        "profile_image": admin_obj.profile_image,
        "stats": [
            { "label": "Active Campaigns", "value": str(total_campaigns) },
            { "label": "Users Managed", "value": f"{users_managed}" },
            { "label": "Uptime", "value": "99.9%" }
        ]
    }

@router.put("/profile")
async def update_admin_profile(
    data: AdminProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    # Verify we are indeed an admin
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
        
    admin_obj = current_admin
    
    admin_obj.name = data.name
    admin_obj.phone = data.phone
    admin_obj.business_name = data.business_name
    admin_obj.gstin = data.gstin
    admin_obj.bio = data.bio
    admin_obj.location = data.location
    
    db.commit()
    return {"message": "Profile updated successfully"}

@router.post("/profile/upload-image")
async def upload_admin_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """Upload profile image for admin"""
    # Verify we are indeed an admin
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if f".{file_extension}" not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, JPEG, PNG, GIF, and WEBP are allowed.")
    
    # Create uploads directory if it doesn't exist
    import os
    upload_dir = "uploads/profile_images"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    import uuid
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Update admin's profile_image field
    admin_obj = current_admin
    admin_obj.profile_image = f"/uploads/profile_images/{unique_filename}"
    db.commit()
    
    return {
        "message": "Profile image uploaded successfully",
        "profile_image_url": admin_obj.profile_image
    }

@router.delete("/profile/delete-image")
async def delete_admin_profile_image(
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """Delete profile image for admin"""
    # Verify we are indeed an admin
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    admin_obj = current_admin
    
    # If there is an existing image, delete the file from disk
    if admin_obj.profile_image:
        import os
        # Path is stored as /uploads/profile_images/...
        # Convert to local path (remove leading slash)
        image_path = admin_obj.profile_image.lstrip('/')
        if os.path.exists(image_path):
             try:
                 os.remove(image_path)
             except Exception as e:
                 print(f"Warning: Failed to delete image file {image_path}: {e}")

    admin_obj.profile_image = None
    db.commit()
    
    return {"message": "Profile image deleted successfully"}

@router.get("/plans")
async def list_plans(
    category: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """ 
    List all available plans with optional category filter.
    Standardized to allow all authenticated users (Admin, Reseller, Business User) to see available plans.
    """
    query = db.query(Plan)
    if category:
        query = query.filter(Plan.plan_category == category.upper())
    return query.all()



@router.post("/plans", status_code=201)
async def create_plan(
    plan_data: PlanCreateRequest, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    # Check if plan name exists
    if db.query(Plan).filter(Plan.name == plan_data.name).first():
        raise HTTPException(status_code=400, detail="Plan name already exists")
    
    new_plan = Plan(
        name=plan_data.name,
        price=plan_data.price,
        credits_offered=plan_data.credits_offered,
        validity_days=plan_data.validity_days,
        deduction_value=plan_data.deduction_value,
        plan_category=plan_data.plan_category.upper()
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    
    # Audit Log
    from services.audit_log_service import AuditLogService
    from schemas.audit_log import AuditLogCreate
    audit_service = AuditLogService(db)
    audit_service.create_log(AuditLogCreate(
        performed_by_id=current_admin.admin_id,
        performed_by_name=current_admin.name or "Admin",
        performed_by_role="admin",
        action_type="CREATE",
        module="Plans",
        description=f"Admin created a new {new_plan.plan_category} plan: {new_plan.name}",
        changes_made=[f"name: {new_plan.name}", f"price: {new_plan.price}", f"credits: {new_plan.credits_offered}"]
    ))
    
    return new_plan

@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: str, 
    data: PlanUpdateRequest, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    if data.name: plan.name = data.name
    if data.price is not None: plan.price = data.price
    if data.credits_offered is not None: plan.credits_offered = data.credits_offered
    if data.validity_days is not None: plan.validity_days = data.validity_days
    if data.deduction_value is not None: plan.deduction_value = data.deduction_value
    if data.plan_category: plan.plan_category = data.plan_category.upper()
    if data.status: plan.status = data.status
    
    db.commit()
    db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted successfully"}

@router.post("/resellers", status_code=201)
async def create_reseller(
    data: ResellerCreateRequest, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    if db.query(Reseller).filter(Reseller.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Optional Plan Check
    plan_name = None
    plan_expiry = None
    offered_credits = 0
    if data.plan_id:
        plan = db.query(Plan).filter(Plan.plan_id == str(data.plan_id), Plan.plan_category == "RESELLER").first()
        if not plan:
            raise HTTPException(status_code=404, detail="Reseller plan not found")
        plan_name = plan.name
        plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
        offered_credits = plan.credits_offered
    
    new_reseller = Reseller(
        name=data.name,
        username=data.username,
        email=data.email,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        business_name=data.business_name,
        role="reseller",
        plan_id=data.plan_id,
        plan_name=plan_name,
        plan_expiry=plan_expiry,
        total_credits=offered_credits,
        available_credits=offered_credits,
        used_credits=0,
        created_by=current_admin.admin_id
    )
    db.add(new_reseller)
    db.commit()
    db.refresh(new_reseller)
    
    # Audit Log
    from services.audit_log_service import AuditLogService
    from schemas.audit_log import AuditLogCreate
    audit_service = AuditLogService(db)
    audit_service.create_log(AuditLogCreate(
        performed_by_id=current_admin.admin_id,
        performed_by_name=current_admin.name or "Admin",
        performed_by_role="admin",
        affected_user_id=new_reseller.reseller_id,
        affected_user_name=new_reseller.name,
        affected_user_email=new_reseller.email,
        action_type="CREATE",
        module="Users",
        description=f"Admin created a new Reseller: {new_reseller.name}",
        changes_made=[f"username: {new_reseller.username}", f"email: {new_reseller.email}"]
    ))
    
    return new_reseller

@router.post("/direct-users", status_code=status.HTTP_201_CREATED)
async def create_direct_user(
    data: BusiUserDirectCreateRequest, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    # 1. Verify Plan
    plan = db.query(Plan).filter(Plan.plan_id == str(data.plan_id), Plan.plan_category == "BUSINESS").first()
    if not plan:
        raise HTTPException(status_code=404, detail="Business plan not found")
    
    # 2. Create User
    new_user = BusiUser(
        name=data.name,
        username=data.username,
        email=data.email,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        business_name=data.business_name,
        parent_role="admin",
        plan_id=plan.plan_id,
        plan_name=plan.name,
        consumption_rate=plan.deduction_value,
        credits_allocated=plan.credits_offered,
        credits_remaining=plan.credits_offered,
        plan_expiry=datetime.now(timezone.utc) + timedelta(days=plan.validity_days),
        created_by=current_admin.admin_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/stats")
async def get_global_stats(
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    total_resellers = db.query(Reseller).count()
    total_direct_users = db.query(BusiUser).filter(BusiUser.parent_role == "admin").count()
    total_indirect_users = db.query(BusiUser).filter(BusiUser.parent_role == "reseller").count()
    
    return {
        "total_resellers": total_resellers,
        "total_direct_users": total_direct_users,
        "total_indirect_users": total_indirect_users,
        "total_businesses": total_direct_users + total_indirect_users
    }

@router.get("/users")
async def list_all_platform_users(
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """Fetch global directory combining directly and indirectly managed users and resellers"""
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    from sqlalchemy.orm import joinedload
    busi_users = db.query(BusiUser).options(joinedload(BusiUser.parent_reseller)).all()
    resellers = db.query(Reseller).all()
    
    final_results = []
    
    # Helper to get creator name
    def get_creator_info(user_obj, is_reseller=False):
        # 1. Check explicit created_by field
        created_by_id = getattr(user_obj, "created_by", None)
        if created_by_id:
            # If created_by is same as ID, it's self-created (rare for this dashboard)
            id_val = getattr(user_obj, "reseller_id" if is_reseller else "busi_user_id", None)
            if id_val and str(created_by_id) == str(id_val):
                return "Self"
            
            # Check Admin
            admin = db.query(MasterAdmin).filter(MasterAdmin.admin_id == created_by_id).first()
            if admin:
                return admin.name or "Admin"
            
            # Check Reseller
            reseller = db.query(Reseller).filter(Reseller.reseller_id == created_by_id).first()
            if reseller:
                return reseller.name
        
        # 2. Fallback for Business Users
        if not is_reseller:
            # Check parent relationship
            if user_obj.parent_reseller:
                return user_obj.parent_reseller.name
            
            # Check parent_role string
            p_role = (user_obj.parent_role or "").strip().lower()
            if p_role == "admin":
                return "Admin"
            if p_role == "reseller" and user_obj.parent_reseller_id:
                # Relationship might not be loaded, try manual lookup
                reseller = db.query(Reseller).filter(Reseller.reseller_id == user_obj.parent_reseller_id).first()
                if reseller:
                    return reseller.name
        
        # 3. Fallback for Resellers (usually created by Admin)
        if is_reseller:
            return "Admin"
            
        return "Unknown"

    for b in busi_users:
        now = datetime.now(timezone.utc)
        plan_expiry = b.plan_expiry
        if plan_expiry and plan_expiry.tzinfo is None:
            plan_expiry = plan_expiry.replace(tzinfo=timezone.utc)
            
        is_expired = plan_expiry < now if plan_expiry else True
        has_credits = (b.credits_remaining or 0) > 0
        
        final_results.append({
            "id": str(b.busi_user_id),
            "name": b.name,
            "email": b.email,
            "role": "Direct Business" if (b.parent_role or "").strip().lower() == "admin" else "Managed User",
            "status": "active" if (has_credits and not is_expired) else "inactive",
            "joined": b.created_at.strftime("%Y-%m-%d") if b.created_at else "Unknown",
            "company": b.business_name or "Independent",
            "plan": b.plan_name or "No Plan Active",
            "created_by_name": get_creator_info(b, is_reseller=False)
        })
        
    for r in resellers:
        final_results.append({
            "id": str(r.reseller_id),
            "name": r.name,
            "email": r.email,
            "role": "Reseller",
            "status": "active" if r.available_credits > 0 else "inactive",
            "joined": r.created_at.strftime("%Y-%m-%d") if r.created_at else "Unknown",
            "company": r.business_name or "Independent Agency",
            "plan": r.plan_name or "No Plan Active",
            "created_by_name": get_creator_info(r, is_reseller=True)
        })
    
    final_results.sort(key=lambda x: x["joined"], reverse=True)
    return final_results

@router.get("/users/{user_id}")
async def get_platform_user_details(
    user_id: str, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 [ADMIN] Fetch comprehensive details for any platform user (Business or Reseller) """
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    # 1. Try BusiUser
    b_user = db.query(BusiUser).filter(BusiUser.busi_user_id == str(user_id)).first()
    if b_user:
        return {
            "id": str(b_user.busi_user_id),
            "role": "Direct Business" if b_user.parent_role == "admin" else "Managed User",
            "status": "active" if b_user.credits_remaining > 0 else "inactive",
            "whatsapp_mode": b_user.whatsapp_mode,
            "plan_name": b_user.plan_name,
            "plan_expiry": b_user.plan_expiry.isoformat() if b_user.plan_expiry else None,
            "profile": {
                "name": b_user.name,
                "email": b_user.email,
                "phone": b_user.phone,
                "username": b_user.username,
                "created_at": b_user.created_at.isoformat() if b_user.created_at else None
            },
            "business": {
                "business_name": b_user.business_name,
                "business_description": b_user.business_description,
                "erp_system": b_user.erp_system,
                "gstin": b_user.gstin
            },
            "address": {
                "full_address": b_user.full_address,
                "pincode": b_user.pincode,
                "country": b_user.country
            },
            "wallet": {
                "credits_allocated": b_user.credits_allocated,
                "credits_used": b_user.credits_used,
                "credits_remaining": b_user.credits_remaining
            }
        }
        
    # 2. Try Reseller
    r_user = db.query(Reseller).filter(Reseller.reseller_id == str(user_id)).first()
    if r_user:
        return {
            "id": str(r_user.reseller_id),
            "role": "Reseller",
            "status": "active" if r_user.available_credits > 0 else "inactive",
            "whatsapp_mode": "reseller_portal",
            "plan_name": r_user.plan_name,
            "plan_expiry": r_user.plan_expiry.isoformat() if r_user.plan_expiry else None,
            "profile": {
                "name": r_user.name,
                "email": r_user.email,
                "phone": r_user.phone,
                "username": r_user.username,
                "created_at": r_user.created_at.isoformat() if r_user.created_at else None
            },
            "business": {
                "business_name": r_user.business_name,
                "business_description": r_user.business_description or "Reseller Enterprise",
                "erp_system": r_user.erp_system or "Internal",
                "gstin": r_user.gstin
            },
            "address": {
                "full_address": r_user.full_address,
                "pincode": r_user.pincode,
                "country": r_user.country
            },
            "wallet": {
                "credits_allocated": r_user.total_credits,
                "credits_used": r_user.used_credits,
                "credits_remaining": r_user.available_credits
            }
        }
        
    raise HTTPException(status_code=404, detail="User not found in platform directory")

@router.delete("/users/{user_id}")
async def delete_platform_user(
    user_id: str, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 [ADMIN] Force delete any platform user (Business or Reseller) """
    # Only Master Admin can perform deletions
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Only Master Admin can delete users")

    try:
        user_id_str = str(user_id)
        
        # 1. Try BusiUser
        busi_user = db.query(BusiUser).filter(BusiUser.busi_user_id == str(user_id)).first()
        if busi_user:
            user_name = busi_user.name
            user_email = busi_user.email
            
            # --- Hierarchical Cleanup for BusiUser ---
            
            # 1. Campaigns Cluster
            campaign_ids = [c.id for c in db.query(Campaign).filter(Campaign.busi_user_id == str(user_id)).all()]
            if campaign_ids:
                db.query(MessageLog).filter(MessageLog.campaign_id.in_(campaign_ids)).delete(synchronize_session=False)
                db.query(CampaignTemplate).filter(CampaignTemplate.campaign_id.in_(campaign_ids)).delete(synchronize_session=False)
                db.query(CampaignDevice).filter(CampaignDevice.campaign_id.in_(campaign_ids)).delete(synchronize_session=False)
                db.query(Campaign).filter(Campaign.id.in_(campaign_ids)).delete(synchronize_session=False)

            # 2. Google Sheets Cluster
            sheet_ids = [s.id for s in db.query(GoogleSheet).filter(GoogleSheet.user_id == str(user_id)).all()]
            if sheet_ids:
                db.query(GoogleSheetTriggerHistory).filter(GoogleSheetTriggerHistory.sheet_id.in_(sheet_ids)).delete(synchronize_session=False)
                db.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.sheet_id.in_(sheet_ids)).delete(synchronize_session=False)
                db.query(GoogleSheet).filter(GoogleSheet.id.in_(sheet_ids)).delete(synchronize_session=False)

            # 3. Devices & Communications Cluster
            device_ids = [d.device_id for d in db.query(Device).filter(Device.busi_user_id == str(user_id)).all()]
            if device_ids:
                db.query(DeviceSession).filter(DeviceSession.device_id.in_(device_ids)).delete(synchronize_session=False)
                db.query(WhatsAppInbox).filter(WhatsAppInbox.device_id.in_(device_ids)).delete(synchronize_session=False)
                db.query(WhatsAppMessages).filter(WhatsAppMessages.device_id.in_(device_ids)).delete(synchronize_session=False)
                db.query(Device).filter(Device.device_id.in_(device_ids)).delete(synchronize_session=False)

            # 4. Global Messaging Logs
            db.query(Message).filter(Message.busi_user_id == str(user_id)).delete(synchronize_session=False)
            db.query(MessageUsageCreditLog).filter(MessageUsageCreditLog.busi_user_id == user_id_str).delete(synchronize_session=False)
            db.query(WhatsAppTemplate).filter(WhatsAppTemplate.busi_user_id == user_id_str).delete(synchronize_session=False)
            db.query(WhatsAppWebhookLog).filter(WhatsAppWebhookLog.busi_user_id == user_id_str).delete(synchronize_session=False)
            
            # 5. Billing & Analytics
            db.query(CreditDistribution).filter(CreditDistribution.to_business_user_id == user_id).delete(synchronize_session=False)
            db.query(BusinessUserAnalytics).filter(BusinessUserAnalytics.business_user_id == user_id).delete(synchronize_session=False)
            
            # 6. Audit Logs (Preserve history but remove ID linkage for safety)
            db.query(AuditLog).filter(AuditLog.affected_user_id == user_id).update({"affected_user_id": None}, synchronize_session=False)

            # 7. Final: Delete User
            db.delete(busi_user)
            
            # Log this action
            from services.audit_log_service import AuditLogService
            from schemas.audit_log import AuditLogCreate
            audit_service = AuditLogService(db)
            audit_service.create_log(AuditLogCreate(
                performed_by_id=current_admin.admin_id,
                performed_by_name=current_admin.name or "Admin",
                performed_by_role="admin",
                affected_user_id=user_id,
                affected_user_name=user_name,
                affected_user_email=user_email,
                action_type="DELETE",
                module="Users",
                description=f"Admin deleted Business User: {user_name}",
                changes_made=[f"user_id: {user_id}"]
            ))
            
            db.commit()
            return {"message": f"Business User {user_name} deleted successfully"}
            
        # 2. Try Reseller
        reseller = db.query(Reseller).filter(Reseller.reseller_id == str(user_id)).first()
        if reseller:
            reseller_name = reseller.name
            reseller_email = reseller.email
            
            # Resellers might have many managed users. 
            # We promote them to 'admin' (Direct) rather than deleting them.
            db.query(BusiUser).filter(BusiUser.parent_reseller_id == user_id).update({
                "parent_reseller_id": None,
                "parent_role": "admin"
            }, synchronize_session=False)
            
            # Cleanup Reseller Analytics & Billing
            db.query(ResellerAnalytics).filter(ResellerAnalytics.reseller_id == user_id).delete(synchronize_session=False)
            db.query(BusinessUserAnalytics).filter(BusinessUserAnalytics.reseller_id == user_id).delete(synchronize_session=False)
            db.query(CreditDistribution).filter(CreditDistribution.from_reseller_id == user_id).delete(synchronize_session=False)
            
            # Audit Logs cleanup
            db.query(AuditLog).filter(AuditLog.reseller_id == user_id).update({"reseller_id": None}, synchronize_session=False)
            
            db.delete(reseller)
            
            # Log this action
            from services.audit_log_service import AuditLogService
            from schemas.audit_log import AuditLogCreate
            audit_service = AuditLogService(db)
            audit_service.create_log(AuditLogCreate(
                performed_by_id=current_admin.admin_id,
                performed_by_name=current_admin.name or "Admin",
                performed_by_role="admin",
                affected_user_id=user_id,
                affected_user_name=reseller_name,
                affected_user_email=reseller_email,
                action_type="DELETE",
                module="Users",
                description=f"Admin deleted Reseller: {reseller_name}",
                changes_made=[f"reseller_id: {user_id}"]
            ))
            
            db.commit()
            return {"message": f"Reseller {reseller_name} deleted successfully"}

        raise HTTPException(status_code=404, detail="User not found in platform directory")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger("ADMIN")
        logger.error(f"❌ [DELETE_USER] Failed to delete user {user_id}: {str(e)}")
        
        detail = str(e)
        if "foreign key constraint" in detail.lower():
            detail = "Cannot delete user: Active records are still referencing this user. Please contact engineering."
            
        raise HTTPException(status_code=400, detail=detail)

@router.put("/users/{user_id}")
async def update_platform_user(
    user_id: str, 
    data: UserUpdateRequest, 
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 [ADMIN] Force update any platform user (Business or Reseller) """
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    # 1. Try BusiUser
    busi_user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
    if busi_user:
        if data.name is not None: busi_user.name = data.name
        if data.email is not None: busi_user.email = data.email
        if data.business_name is not None: busi_user.business_name = data.business_name
        
        # 🔥 FIX: Sync Plan if updated by admin
        if data.plan_id:
            plan = db.query(Plan).filter(Plan.plan_id == data.plan_id).first()
            if plan:
                busi_user.plan_id = plan.plan_id
                busi_user.plan_name = plan.name
                busi_user.consumption_rate = plan.deduction_value
                # If credits not explicitly provided, use plan default
                if data.credits_allocated is None:
                    busi_user.credits_allocated = plan.credits_offered
                    busi_user.credits_remaining = plan.credits_offered
                busi_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)
        
        if data.credits_allocated is not None:
            busi_user.credits_allocated = data.credits_allocated
            busi_user.credits_remaining = data.credits_allocated

        db.commit()
        db.refresh(busi_user)
        return {"message": f"Business User {busi_user.name} updated successfully"}
        
    # 2. Try Reseller
    reseller = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
    if reseller:
        if data.name is not None: reseller.name = data.name
        if data.email is not None: reseller.email = data.email
        if data.business_name is not None: reseller.business_name = data.business_name
        
        # 🔥 FIX: Sync Plan for Reseller
        if data.plan_id:
            plan = db.query(Plan).filter(Plan.plan_id == data.plan_id).first()
            if plan:
                reseller.plan_id = plan.plan_id
                reseller.plan_name = plan.name
                if data.credits_allocated is None:
                    reseller.total_credits = plan.credits_offered
                    reseller.available_credits = plan.credits_offered
                reseller.plan_expiry = datetime.now(timezone.utc) + timedelta(days=plan.validity_days)

        if data.credits_allocated is not None:
            reseller.total_credits = data.credits_allocated
            reseller.available_credits = data.credits_allocated

        db.commit()
        db.refresh(reseller)
        return {"message": f"Reseller {reseller.name} updated successfully"}
        
    raise HTTPException(status_code=404, detail="User not found in platform directory")

@router.get("/resellers")
async def list_resellers(
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    resellers = db.query(Reseller).all()
    results = []
    for r in resellers:
        user_count = db.query(BusiUser).filter(BusiUser.parent_reseller_id == r.reseller_id).count()
        results.append({
            "reseller_id": r.reseller_id,
            "name": r.name,
            "email": r.email,
            "user_count": user_count,
            "credits": r.available_credits
        })
    return results

@router.get("/analytics")
async def get_admin_analytics(
    reseller_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 [ADMIN PLATFORM ANALYTICS] Global hierarchy and user lifecycle oversight """
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    from models.message import Message, MessageStatus
    from models.payment_order import PaymentOrder
    from models.reseller import Reseller
    from models.busi_user import BusiUser
    from sqlalchemy import func
    
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    
    # 1. Platform Hierarchy Counts (Top Cards)
    total_resellers = db.query(Reseller).count()
    total_direct_users = db.query(BusiUser).filter(BusiUser.parent_role == "admin").count()
    total_indirect_users = db.query(BusiUser).filter(BusiUser.parent_role == "reseller").count()
    
    # Message query with reseller filtering
    msg_base_query = db.query(Message)
    if reseller_id:
        msg_base_query = msg_base_query.join(BusiUser, BusiUser.busi_user_id == Message.busi_user_id) \
                                       .filter(BusiUser.parent_reseller_id == reseller_id)
    
    total_messages = msg_base_query.count()
    
    # 2. Reseller Breakdown (How many users under each)
    reseller_data = db.query(
        Reseller.name,
        Reseller.email,
        Reseller.available_credits,
        func.count(BusiUser.busi_user_id).label('user_count')
    ).outerjoin(BusiUser, Reseller.reseller_id == BusiUser.parent_reseller_id) \
     .group_by(Reseller.reseller_id).all()
     
    reseller_list = [
        {
            "name": r.name,
            "email": r.email,
            "credits": r.available_credits,
            "managed_users": r.user_count
        } for r in reseller_data
    ]
    
    # 3. User Expiry Watchlist (Direct/Indirect Users & Resellers nearing expiry)
    expiry_watchlist = db.query(
        BusiUser.name,
        BusiUser.parent_role.label('role'),
        BusiUser.plan_name,
        BusiUser.plan_expiry
    ).filter(BusiUser.plan_expiry.isnot(None)).order_by(BusiUser.plan_expiry.asc()).limit(10).all()
    
    reseller_watchlist = db.query(
        Reseller.name,
        Reseller.role,
        Reseller.plan_name,
        Reseller.plan_expiry
    ).filter(Reseller.plan_expiry.isnot(None)).order_by(Reseller.plan_expiry.asc()).limit(10).all()
    
    merged_list = []
    
    for u in expiry_watchlist:
        expiry = u.plan_expiry
        if expiry and expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
            
        merged_list.append({
            "name": u.name,
            "type": "Direct Business" if u.role == "admin" else "Indirect Business",
            "plan": u.plan_name or "Custom Plan",
            "expires_at": expiry.strftime('%Y-%m-%d') if expiry else "Never",
            "raw_expiry": expiry
        })
        
    for r in reseller_watchlist:
        expiry = r.plan_expiry
        if expiry and expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
            
        merged_list.append({
            "name": r.name,
            "type": "Reseller",
            "plan": r.plan_name or "Reseller Plan",
            "expires_at": expiry.strftime('%Y-%m-%d') if expiry else "Never",
            "raw_expiry": expiry
        })
        
    merged_list.sort(key=lambda x: x["raw_expiry"] if x["raw_expiry"] else datetime.max.replace(tzinfo=timezone.utc))
    watchlist = merged_list[:10]
    
    # 4. Message Usage Categories
    campaign_count = msg_base_query.filter(Message.message_type == MessageType.TEMPLATE).count()
    api_count = msg_base_query.filter(Message.message_type != MessageType.TEMPLATE).count()
    
    # 5. Global Message Performance (Graph)
    from sqlalchemy import extract
    current_year = now.year
    
    graph_query = db.query(
        extract('month', Message.sent_at).label('month'),
        func.count(Message.message_id).label('total'),
        func.count(Message.message_id).filter(Message.status.in_([MessageStatus.DELIVERED, MessageStatus.READ])).label('delivered')
    )
    
    if reseller_id:
        graph_query = graph_query.join(BusiUser, BusiUser.busi_user_id == Message.busi_user_id) \
                                 .filter(BusiUser.parent_reseller_id == reseller_id)
        
    stats = graph_query.filter(
        extract('year', Message.sent_at) == current_year
    ).group_by('month').order_by('month').all()
    
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    graph_data = []
    stats_dict = {int(s.month): s for s in stats}
    
    for i in range(1, 13):
        m_stat = stats_dict.get(i)
        graph_data.append({
            "name": month_names[i-1],
            "sent": m_stat.total if m_stat else 0,
            "delivered": m_stat.delivered if m_stat else 0
        })

    return {
        "kpis": {
            "total_resellers": total_resellers,
            "direct_business_users": total_direct_users,
            "indirect_business_users": total_indirect_users,
            "total_platform_messages": total_messages
        },
        "reseller_hierarchy": reseller_list,
        "user_expiry_watchlist": watchlist,
        "usage_breakdown": {
            "whatsapp_campaigns": campaign_count,
            "api_requests": api_count
        },
        "graph_data": graph_data,
        "user_type_breakdown": [
            {"name": "Resellers", "value": total_resellers},
            {"name": "Sub-Biz", "value": total_indirect_users},
            {"name": "Direct Biz", "value": total_direct_users},
        ],
        "plan_distribution": [
            {"name": plan, "value": count}
            for plan, count in db.query(BusiUser.plan_name, func.count(BusiUser.busi_user_id))
            .filter(BusiUser.plan_name.isnot(None))
            .group_by(BusiUser.plan_name).all()
        ],
        "reseller_credits": [
            {"name": r.name, "value": r.available_credits}
            for r in reseller_data
        ],
        "reseller_users": [
            {"name": r.name, "value": r.user_count}
            for r in reseller_data
        ]
    }

@router.get("/orders")
async def list_all_orders(
    user_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 [ADMIN] List all systems orders with enhanced user details """
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    from models.payment_order import PaymentOrder
    
    query = db.query(PaymentOrder)
    
    # 1. Filters
    if user_type:
        query = query.filter(PaymentOrder.user_type == user_type.lower())
    if status:
        query = query.filter(PaymentOrder.status == status.lower())
    if start_date:
        query = query.filter(PaymentOrder.created_at >= start_date)
    if end_date:
        query = query.filter(PaymentOrder.created_at <= end_date)
        
    orders = query.order_by(PaymentOrder.created_at.desc()).offset(skip).limit(limit).all()
    
    # 2. Enrich with Names
    results = []
    for o in orders:
        purchaser_name = "System/Unknown"
        allocated_name = None
        
        # Look up purchaser
        if o.user_type == "business":
            user = db.query(BusiUser).filter(BusiUser.busi_user_id == o.user_id).first()
            if user: purchaser_name = user.business_name or user.name
        elif o.user_type == "reseller":
            reseller = db.query(Reseller).filter(Reseller.reseller_id == o.user_id).first()
            if reseller: purchaser_name = reseller.name or reseller.business_name
        elif o.user_type == "admin":
            purchaser_name = "Master Admin"
            
        # Look up allocated to
        if o.allocated_to_user_id:
            target_user = db.query(BusiUser).filter(BusiUser.busi_user_id == o.allocated_to_user_id).first()
            if target_user:
                allocated_name = target_user.business_name or target_user.name
            else:
                # Might be a reseller? Usually it's busi_user
                target_reseller = db.query(Reseller).filter(Reseller.reseller_id == o.allocated_to_user_id).first()
                if target_reseller:
                    allocated_name = target_reseller.name
                else:
                    allocated_name = str(o.allocated_to_user_id)
        
        results.append({
            "id": str(o.id),
            "txnid": o.txnid,
            "plan_name": o.plan_name,
            "credits": o.credits,
            "amount": o.amount,
            "status": o.status,
            "user_type": o.user_type,
            "purchaser_name": purchaser_name,
            "allocated_to_user_id": str(o.allocated_to_user_id) if o.allocated_to_user_id else None,
            "allocated_to_name": allocated_name,
            "is_allocated": o.is_allocated or "pending",
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "razorpay_payment_id": o.razorpay_payment_id
        })
        
    return results

@router.get("/audit-logs")
async def get_admin_audit_logs(
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ Fetch all system-wide audit activities for Admin Dashboard """
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    from services.audit_log_service import AuditLogService
    service = AuditLogService(db)
    
    logs, total, filtered = service.get_logs(
        reseller_id=None, # None means ALL for Admin
        module=module,
        action=action,
        search=search,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    last_activity = service.get_last_activity_days_ago(None)
    
    return {
        "total": total,
        "filtered": filtered,
        "last_activity_days_ago": last_activity,
        "logs": [
            {
                "id": str(log.log_id),
                "action_type": log.action_type,
                "module": log.module,
                "performed_by_name": log.performed_by_name or "System",
                "performed_by_role": log.performed_by_role or "system",
                "affected_user_name": log.affected_user_name or "N/A",
                "affected_user_email": log.affected_user_email or "N/A",
                "description": log.description or "",
                "changes_made": log.changes_made or [],
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            } for log in logs
        ]
    }

class GiveCreditsRequest(BaseModel):
    user_id: str
    user_type: str # 'reseller' or 'business'
    credits: int
    description: Optional[str] = "Manual credit addition by Admin"

@router.post("/resolve-order/{order_id}")
async def resolve_order_manually(
    order_id: str,
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 [ADMIN] Force success of a pending order to restore missing credits """
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    from models.payment_order import PaymentOrder
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status == "success" and order.is_allocated == "allocated":
        return {"message": "Order is already completed and allocated"}
        
    # Mark as success if pending
    order.status = "success"
    
    # 1. Logic for credit allocation
    target_id = order.allocated_to_user_id or order.user_id
    
    # Try BusiUser
    target_user = db.query(BusiUser).filter(BusiUser.busi_user_id == target_id).first()
    is_reseller = False
    
    if not target_user:
        target_user = db.query(Reseller).filter(Reseller.reseller_id == target_id).first()
        is_reseller = True
        
    if target_user:
        if not is_reseller:
            target_user.credits_remaining = (target_user.credits_remaining or 0) + order.credits
            target_user.credits_allocated = (target_user.credits_allocated or 0) + order.credits
            target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)
            current_balance = target_user.credits_remaining
        else:
            target_user.available_credits = (target_user.available_credits or 0) + order.credits
            target_user.total_credits = (target_user.total_credits or 0) + order.credits
            target_user.plan_expiry = datetime.now(timezone.utc) + timedelta(days=365)
            current_balance = target_user.available_credits
            
        # Log the addition
        from models.message_usage import MessageUsageCreditLog
        import uuid
        alloc_log = MessageUsageCreditLog(
            usage_id=f"manual-{uuid.uuid4().hex[:8]}",
            busi_user_id=str(target_id),
            message_id=f"ADMIN-RESOLVE-{order.txnid}",
            credits_deducted=-order.credits,
            balance_after=current_balance,
            timestamp=datetime.now()
        )
        db.add(alloc_log)
        # Audit Log
        from services.audit_log_service import AuditLogService
        from schemas.audit_log import AuditLogCreate
        audit_service = AuditLogService(db)
        audit_service.create_log(AuditLogCreate(
            performed_by_id=current_admin.admin_id,
            performed_by_name=current_admin.name or "Admin",
            performed_by_role="admin",
            affected_user_id=target_id,
            affected_user_name=target_user.name,
            affected_user_email=target_user.email,
            action_type="MANUAL RESOLVE",
            module="Billing",
            description=f"Admin manually resolved order {order.txnid}. {order.credits} credits added to {target_user.name}.",
            changes_made=[f"order_status: success", f"credits: +{order.credits}"]
        ))
        
        db.commit()
        return {"message": f"Order {order.txnid} successfully resolved. {order.credits} credits added to {target_user.name}"}
    
    db.commit()
    return {"message": "Order marked as success, but no target profile found for credit allocation."}

@router.post("/give-credits")
async def give_credits_to_user(
    data: GiveCreditsRequest,
    db: Session = Depends(get_db),
    current_admin: MasterAdmin = Depends(get_current_user)
):
    """ 🔥 [ADMIN] Directly grant credits to any user (Reseller or Business) """
    if not isinstance(current_admin, MasterAdmin):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    target_user = None
    role_name = ""
    
    if data.user_type == "reseller":
        target_user = db.query(Reseller).filter(Reseller.reseller_id == data.user_id).first()
        role_name = "Reseller"
    else:
        target_user = db.query(BusiUser).filter(BusiUser.busi_user_id == data.user_id).first()
        role_name = "Business User"
        
    if not target_user:
        raise HTTPException(status_code=404, detail=f"{role_name} with ID {data.user_id} not found")
        
    try:
        # Add credits
        if data.user_type == "reseller":
            target_user.available_credits = (target_user.available_credits or 0) + data.credits
            target_user.total_credits = (target_user.total_credits or 0) + data.credits
            current_balance = target_user.available_credits
        else:
            target_user.credits_remaining = (target_user.credits_remaining or 0) + data.credits
            target_user.credits_allocated = (target_user.credits_allocated or 0) + data.credits
            current_balance = target_user.credits_remaining
            
        # Log the gift
        from models.message_usage import MessageUsageCreditLog
        import uuid
        gift_log = MessageUsageCreditLog(
            usage_id=f"gift-{uuid.uuid4().hex[:8]}",
            busi_user_id=str(data.user_id),
            message_id=f"ADMIN-GIFT",
            credits_deducted=-data.credits,
            balance_after=current_balance,
            timestamp=datetime.now()
        )
        db.add(gift_log)
        
        # Audit Log
        from services.audit_log_service import AuditLogService
        from schemas.audit_log import AuditLogCreate
        audit_service = AuditLogService(db)
        audit_service.create_log(AuditLogCreate(
            performed_by_id=current_admin.admin_id,
            performed_by_name=current_admin.name or "Admin",
            performed_by_role="admin",
            affected_user_id=data.user_id,
            affected_user_name=target_user.name,
            affected_user_email=target_user.email,
            action_type="CREDIT GIFT",
            module="Billing",
            description=f"Admin gifted {data.credits} credits to {target_user.name}. Reason: {data.description}",
            changes_made=[f"credits: +{data.credits}"]
        ))
        
        db.commit()
        return {"message": f"Successfully granted {data.credits} credits to {target_user.name}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to grant credits: {str(e)}")
