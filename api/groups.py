from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import uuid
import logging
import re

from db.session import get_db
from api.busi_user import get_current_busi_user_id
from models.busi_user import BusiUser
from models.contact_group import ContactGroup, Contact
from services.whatsapp_service import WhatsAppService
from services.group_service import GroupService
from models.admin import MasterAdmin
from models.reseller import Reseller
from schemas.whatsapp import MessageRequest
from services.whatsapp_engine_service import WhatsAppEngineService


# Dependency to get current user object
def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_busi_user_id)
) -> Any:
    # 1. Try BusiUser
    user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
    if user:
        return user
    
    # 2. Try Admin (MasterAdmin)
    admin = db.query(MasterAdmin).filter(MasterAdmin.admin_id == user_id).first()
    if admin:
        return BusiUser(
            busi_user_id=admin.admin_id,
            name=admin.name or "System Admin",
            email=admin.email,
            role="admin",
            status="active"
        )
    
    # 3. Try Reseller
    res = db.query(Reseller).filter(Reseller.reseller_id == user_id).first()
    if res:
         return BusiUser(
            busi_user_id=res.reseller_id,
            name=res.name or "Reseller",
            email=res.email,
            role="reseller",
            status="active",
            parent_reseller_id=res.reseller_id
        )

    raise HTTPException(status_code=404, detail="User not found")

router = APIRouter(tags=["Groups"])

logger = logging.getLogger(__name__)

# Pydantic Schemas
class GroupSchema(BaseModel):
    group_id: str
    name: str
    contact_count: int
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CreateGroupRequest(BaseModel):
    name: str
    description: Optional[str] = None

class ContactItem(BaseModel):
    name: str
    phone: str

    @field_validator('phone')
    def validate_phone(cls, v):
        # Basic validation: must contain digits, may start with +
        if not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Invalid phone number format. Must be 10-15 digits.')
        return v

class AddContactsRequest(BaseModel):
    contacts: List[ContactItem]

class SendMessageRequest(BaseModel):
    group_ids: List[str]
    # For text messages
    message: Optional[str] = None
    # For template messages
    template_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    language_code: Optional[str] = "en_US"
    
    channel: Optional[str] = "unofficial"  # "official" or "unofficial"

class SendMessageResponse(BaseModel):
    success: bool
    total_groups: int
    total_contacts: int
    sent: int
    failed: int

class ScanGroupsResponse(BaseModel):
    success: bool
    groups: List[Dict[str, Any]]
    total: int

class ExportGroupMembersRequest(BaseModel):
    group_name: str
    device_id: str

@router.get("/", response_model=List[GroupSchema])
def get_groups(
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """List all contact groups for the current user."""
    try:
        from db.base import engine
        from models.contact_group import ContactGroup, Contact, group_contacts
        ContactGroup.metadata.create_all(bind=engine)

        group_service = GroupService(db)
        groups = group_service.get_user_groups(current_user.busi_user_id)
        
        result = []
        for g in groups:
            # Calculate contact count
            result.append(GroupSchema(
                group_id=g.group_id,
                name=g.name,
                contact_count=len(g.contacts),
                description=g.description
            ))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve groups")

@router.post("/create", response_model=GroupSchema)
def create_group(
    payload: CreateGroupRequest,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Create a new contact group."""
    try:
        group_service = GroupService(db)
        group = group_service.create_group(
            user_id=current_user.busi_user_id,
            name=payload.name,
            description=payload.description
        )
        
        return GroupSchema(
            group_id=group.group_id,
            name=group.name,
            contact_count=0,
            description=group.description
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create group")

@router.get("/{group_id}/contacts", response_model=List[ContactItem])
def get_group_members(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Get all contacts in a group."""
    group = db.query(ContactGroup).filter(
        ContactGroup.group_id == group_id,
        ContactGroup.user_id == current_user.busi_user_id
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    contacts = []
    for c in group.contacts:
        contacts.append(ContactItem(name=c.name or "", phone=c.phone))
        
    return contacts

@router.post("/{group_id}/contacts")
def add_contacts(
    group_id: str,
    payload: AddContactsRequest,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Add multiple contacts to a group."""
    try:
        group_service = GroupService(db)
        
        # Convert contacts to dict format for service
        contact_data = [
            {"name": contact.name, "phone": contact.phone}
            for contact in payload.contacts
        ]
        
        return group_service.add_contacts_to_group(
            group_id=group_id,
            user_id=current_user.busi_user_id,
            contact_data=contact_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add contacts to group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add contacts")

@router.delete("/{group_id}/contacts/{phone}")
def remove_contact_from_group(
    group_id: str,
    phone: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Remove a specific contact from a group by phone number."""
    try:
        group = db.query(ContactGroup).filter(
            ContactGroup.group_id == group_id,
            ContactGroup.user_id == current_user.busi_user_id
        ).first()
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
            
        contact = db.query(Contact).filter(
            Contact.phone == phone,
            Contact.user_id == current_user.busi_user_id
        ).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
            
        if contact in group.contacts:
            group.contacts.remove(contact)
            db.commit()
            return {"success": True, "message": "Contact removed from group"}
        else:
            raise HTTPException(status_code=404, detail="Contact not found in this group")
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to remove contact {phone} from group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove contact")

@router.delete("/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Delete a contact group and all its contacts."""
    try:
        group_service = GroupService(db)
        group_service.delete_group(group_id, current_user.busi_user_id)
        return {"success": True, "message": "Group deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete group")

@router.post("/send-message", response_model=SendMessageResponse)
def send_group_message(
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    logger.info(f"Received group message request from user {current_user.busi_user_id} via {payload.channel}")
    """
    Send a message to all contacts in the selected groups.
    Deduplicates contacts by phone number.
    Support for 'official' and 'unofficial' channels.
    """
    if not payload.group_ids:
        raise HTTPException(status_code=400, detail="No groups selected")
    
    if not payload.message and not payload.template_name:
        raise HTTPException(status_code=400, detail="Either message or template_name is required")

    # 1. Fetch requested groups belonging to user
    groups = db.query(ContactGroup).filter(
        ContactGroup.group_id.in_(payload.group_ids),
        ContactGroup.user_id == current_user.busi_user_id
    ).all()
    
    if not groups:
        return SendMessageResponse(
            success=False, total_groups=0, total_contacts=0, sent=0, failed=0
        )

    # 2. Collect unique active contacts (by phone number)
    unique_phones = set()
    for g in groups:
        for contact in g.contacts:
            if contact.phone:
                unique_phones.add(contact.phone)
    
    total_contacts = len(unique_phones)
    sent_count = 0
    failed_count = 0
    
    # 3. Send logic based on channel
    if payload.channel == "official":
        from services.official_whatsapp_config_service import OfficialWhatsAppConfigService
        official_service = OfficialWhatsAppConfigService(db)
        
        # Get official config
        config = official_service.get_config_by_user_id(str(current_user.busi_user_id))
        if not config or not config.is_active:
             raise HTTPException(
                status_code=400, 
                detail="Official WhatsApp configuration not found or inactive. Please configure it in Settings."
            )
            
        for phone in unique_phones:
            try:
                # Use Official API
                if payload.template_name:
                    resp = official_service.send_template_message(
                        config=config,
                        to_number=phone,
                        template_name=payload.template_name,
                        template_data=payload.template_data or {},
                        language_code=payload.language_code
                    )
                elif payload.message:
                    resp = official_service.send_text_message(
                        config=config,
                        to_number=phone,
                        content=payload.message
                    )
                else:
                    # Should trigger earlier validation, but safe fallback
                    continue

                if resp.success:
                    sent_count += 1
                else:
                    logger.error(f"Failed to send official message to {phone}: {resp.error_message}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"Exception sending official message to {phone}: {e}")
                failed_count += 1
                
    else:
        # Default to Unofficial (Engine)
        whatsapp_service = WhatsAppService(db)
        
        for phone in unique_phones:
            try:
                req = MessageRequest(
                    user_id=str(current_user.busi_user_id),
                    receiver_number=phone,
                    message_text=payload.message
                )
                # Use send_message_via_engine to handle credits and device selection
                whatsapp_service.send_message_via_engine(req)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {phone}: {e}")
                failed_count += 1
                # Continue to next contact (no rollback of batch)

    return SendMessageResponse(
        success=True,
        total_groups=len(groups),
        total_contacts=total_contacts,
        sent=sent_count,
        failed=failed_count
    )

@router.get("/whatsapp/scan", response_model=ScanGroupsResponse)
def scan_whatsapp_groups(
    device_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Scan all groups from the connected WhatsApp device."""
    try:
        engine_service = WhatsAppEngineService(db)
        
        # Check device status first to avoid unnecessary requests
        device_status = engine_service.check_device_status(device_id)
        if device_status.get("status") != "connected":
            raise HTTPException(
                status_code=400, 
                detail=f"Device not connected: {device_status.get('status', 'Unknown')}"
            )
        
        # Use the proper rate-limited request method
        result = engine_service._make_request_with_retry("GET", f"/session/{device_id}/groups")
        
        if result and result.status_code == 200:
            data = result.json()
            if data.get("success"):
                return ScanGroupsResponse(
                    success=True,
                    groups=data.get("groups", []),
                    total=data.get("total", 0)
                )
        
        raise HTTPException(status_code=400, detail="Failed to scan groups from engine")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning WhatsApp groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whatsapp/export")
def export_whatsapp_group_members(
    payload: ExportGroupMembersRequest,
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Export group members from WhatsApp engine as JSON."""
    try:
        engine_service = WhatsAppEngineService(db)
        
        # Check device status first to avoid unnecessary requests
        device_status = engine_service.check_device_status(payload.device_id)
        if device_status.get("status") != "connected":
            raise HTTPException(
                status_code=400, 
                detail=f"Device not connected: {device_status.get('status', 'Unknown')}"
            )
        
        # Use the proper rate-limited request method
        result = engine_service._make_request_with_retry(
            "POST", 
            f"/session/{payload.device_id}/group-members",
            json={"group_name": payload.group_name}
        )
        
        if result and result.status_code == 200:
            data = result.json()
            if data.get("success"):
                # Extract members and format for frontend
                members = data.get("members", [])
                formatted_members = [
                    {
                        "name": member.get("name", ""),
                        "phone": member.get("phone", "")
                    }
                    for member in members
                ]
                return {
                    "members": formatted_members,
                    "group_id": data.get("group_id"),
                    "group_name": data.get("group_name"),
                    "total": data.get("total", 0)
                }
        
        raise HTTPException(status_code=400, detail="Failed to export group members from engine")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting WhatsApp group members: {e}")
        raise HTTPException(status_code=500, detail=str(e))
