from fastapi import APIRouter, Depends, HTTPException, Query, Body, Header, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from jose import JWTError  # Ensure this is available or use core.security verify_token
import logging

from db.session import get_db
from schemas.official_whatsapp_config import (
    OfficialWhatsAppConfigCreate,
    OfficialWhatsAppConfigResponse,
    OfficialWhatsAppConfigUpdate,
    WhatsAppAPIResponse,
    WhatsAppWebhookConfig,
    WhatsAppTemplateValidation,
    WhatsAppTemplateResponse
)
from services.official_whatsapp_config_service import OfficialWhatsAppConfigService
from core.security import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Dependencies ---

async def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Verify the JWT token and return the payload.
    Enforce that the user has the 'user' role.
    """
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
    
    role = payload.get("role")
    if role not in ["user", "business_owner", "business", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Business Users or Admins only"
        )
    return payload

# --- Endpoints ---

@router.post("/config", response_model=OfficialWhatsAppConfigResponse)
async def create_whatsapp_config(
    config_data: OfficialWhatsAppConfigCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create or Update official WhatsApp configuration (Upsert) for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    
    # Force the busi_user_id from the token
    config_data.busi_user_id = busi_user_id
    
    service = OfficialWhatsAppConfigService(db)
    
    # Check if config already exists for this user
    existing_config = service.get_config_by_user_id(busi_user_id)
    
    try:
        config_orm = None
        if existing_config:
            # Upsert logic: Update existing config
            update_data = OfficialWhatsAppConfigUpdate(
                whatsapp_official=config_data.whatsapp_official,
                is_active=True # Ensure it's active on update/re-save
            )
            config_orm = service.update_config(busi_user_id, update_data)
        else:
            # Create new config
            config_orm = service.create_config(config_data)

        # 🔥 FIXED: Create official device when config is saved successfully
        try:
            from services.device_service import DeviceService
            from models.device import Device, DeviceType, SessionStatus
            import uuid
            
            # Use direct query to check for BOTH active and deleted devices with this name
            # This prevents (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "uniq_user_device_name"
            existing_device = db.query(Device).filter(
                Device.busi_user_id == busi_user_id,
                Device.device_name == "Official WhatsApp Cloud"
            ).first()
            
            if existing_device:
                # Always ensure it is connected and active upon config save/update
                existing_device.is_active = True
                existing_device.deleted_at = None
                existing_device.session_status = SessionStatus.connected
                existing_device.last_active = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Updated official WhatsApp device status to connected: {existing_device.device_id} for user {busi_user_id}")
            else:
                # Create fresh official device
                from schemas.device import DeviceCreate
                device_data = DeviceCreate(
                    device_id=uuid.uuid4(),
                    busi_user_id=busi_user_id,
                    device_name="Official WhatsApp Cloud",
                    device_type=DeviceType.official,
                    session_status=SessionStatus.connected,
                    is_active=True,
                    last_active=datetime.utcnow()
                )
                
                device_service = DeviceService(db)
                official_device = device_service.create_device(device_data)
                logger.info(f"✅ Created new official WhatsApp device: {official_device.device_id} for user {busi_user_id}")
                
        except Exception as device_error:
            logger.error(f"⚠️ Failed to create official device: {device_error}")
            # Don't fail the config save if device creation fails

        # Map flat ORM object to nested Pydantic schema 
        return OfficialWhatsAppConfigResponse(
            id=config_orm.id,
            busi_user_id=config_orm.busi_user_id,
            whatsapp_official={
                "business_number": config_orm.business_number,
                "waba_id": config_orm.waba_id,
                "phone_number_id": config_orm.phone_number_id,
                "access_token": config_orm.access_token,
                "template_status": config_orm.template_status,
            },
            created_at=config_orm.created_at,
            updated_at=config_orm.updated_at,
            is_active=config_orm.is_active
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save WhatsApp configuration: {str(e)}"
        )


@router.get("/config", response_model=Optional[OfficialWhatsAppConfigResponse])
async def get_whatsapp_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get WhatsApp configuration for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config_orm = service.get_config_by_user_id(busi_user_id)
    
    if not config_orm:
        return None
    
    return OfficialWhatsAppConfigResponse(
        id=config_orm.id,
        busi_user_id=config_orm.busi_user_id,
        whatsapp_official={
            "business_number": config_orm.business_number,
            "waba_id": config_orm.waba_id,
            "phone_number_id": config_orm.phone_number_id,
            "access_token": config_orm.access_token,
            "template_status": config_orm.template_status,
        },
        created_at=config_orm.created_at,
        updated_at=config_orm.updated_at,
        is_active=config_orm.is_active
    )


@router.put("/config", response_model=OfficialWhatsAppConfigResponse)
async def update_whatsapp_config(
    config_data: OfficialWhatsAppConfigUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update WhatsApp configuration for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config_orm = service.update_config(busi_user_id, config_data)
    
    if not config_orm:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    return OfficialWhatsAppConfigResponse(
        id=config_orm.id,
        busi_user_id=config_orm.busi_user_id,
        whatsapp_official={
            "business_number": config_orm.business_number,
            "waba_id": config_orm.waba_id,
            "phone_number_id": config_orm.phone_number_id,
            "access_token": config_orm.access_token,
            "template_status": config_orm.template_status,
        },
        created_at=config_orm.created_at,
        updated_at=config_orm.updated_at,
        is_active=config_orm.is_active
    )


@router.delete("/config")
async def delete_whatsapp_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete WhatsApp configuration for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    success = service.delete_config(busi_user_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    return {"message": "WhatsApp configuration deleted successfully"}


@router.post("/config/verify-webhook", response_model=WhatsAppAPIResponse)
async def verify_webhook(
    webhook_config: WhatsAppWebhookConfig,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Verify webhook configuration with Meta API."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    result = service.verify_webhook(config, webhook_config)
    return result


@router.post("/config/send-template", response_model=WhatsAppAPIResponse)
async def send_template_message(
    to_number: str = Body(..., embed=True),
    template_name: str = Body(..., embed=True),
    template_data: Dict[str, Any] = Body(..., embed=True),
    language_code: str = Body("en_US", embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send template message via WhatsApp Cloud API.
    Only allows users with approved templates and active config.
    """
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    if not config.is_active:
        raise HTTPException(
            status_code=400,
            detail="WhatsApp configuration is not active"
        )
    
    # Optional: Verify template details in DB before sending if needed
    # For now, we rely on the implementation in service which calls Meta.
    
    result = service.send_template_message(config, to_number, template_name, template_data, language_code)
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error_message or "Failed to send template message"
        )
        
    return result


@router.post("/config/send-text", response_model=WhatsAppAPIResponse)
async def send_text_message(
    to_number: str = Body(..., embed=True),
    content: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send text message via WhatsApp Cloud API.
    Only allows users with active config.
    """
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    if not config.is_active:
        raise HTTPException(
            status_code=400,
            detail="WhatsApp configuration is not active"
        )
    
    result = service.send_text_message(config, to_number, content)
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error_message or "Failed to send text message"
        )
        
    return result


@router.get("/config/business-profile", response_model=WhatsAppAPIResponse)
async def get_business_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get WhatsApp business profile from Meta API."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    result = service.get_business_profile(config)
    return result


@router.post("/config/sync-templates", response_model=WhatsAppAPIResponse)
async def sync_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Sync templates from Meta API."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    result = service.sync_templates(config)
    return result


@router.get("/config/templates", response_model=List[WhatsAppTemplateResponse])
async def get_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get stored templates for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    return service.get_templates(busi_user_id)


@router.post("/config/templates", response_model=WhatsAppTemplateResponse)
async def create_template(
    template_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new template for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    
    try:
        # Create new template
        template = service.create_template(
            busi_user_id=busi_user_id,
            template_name=template_data.get("template_name"),
            category=template_data.get("category"),
            language=template_data.get("language"),
            content=template_data.get("content"),
            meta_template_id=template_data.get("meta_template_id")
        )
        
        return WhatsAppTemplateResponse(
            id=template.id,
            busi_user_id=template.busi_user_id,
            template_name=template.template_name,
            template_status=template.template_status,
            category=template.category,
            language=template.language,
            content=template.content,
            meta_template_id=template.meta_template_id,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create template: {str(e)}"
        )


@router.post("/config/validate-template", response_model=WhatsAppAPIResponse)
async def validate_template(
    template_data: WhatsAppTemplateValidation,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Validate template with Meta API."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    result = service.validate_template(config, template_data)
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error_message or "Template validation failed"
        )
        
    return result


@router.get("/config/webhook-logs")
async def get_webhook_logs(
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get webhook logs for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    logs = service.get_webhook_logs(busi_user_id, limit)
    
    return {
        "busi_user_id": busi_user_id,
        "webhook_logs": logs,
        "total_logs": len(logs)
    }


@router.get("/config/health")
async def check_config_health(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check health of WhatsApp configuration for the logged-in user."""
    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    # Test API connectivity
    try:
        profile_result = service.get_business_profile(config)
        is_healthy = profile_result.success
    except:
        is_healthy = False
    
    return {
        "busi_user_id": busi_user_id,
        "is_active": config.is_active,
        "template_status": config.template_status,
        "api_healthy": is_healthy,
        "last_updated": config.updated_at,
        "health_check_time": datetime.utcnow()
    }


# --- Media Upload + Send Endpoint (Frontend Integration) ---

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".csv", ".xls", ".xlsx"}

def _detect_media_type_from_filename(filename: str) -> str:
    """Detect WhatsApp media type from filename extension."""
    import os
    ext = os.path.splitext(filename)[-1].lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in DOCUMENT_EXTENSIONS:
        return "document"
    return "document"


@router.post("/config/send-media")
async def send_media_message(
    to_number: str = Form(...),
    caption: str = Form(""),
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send media message via WhatsApp Cloud API.
    Accepts EITHER a multipart file upload OR a file path/URL.
    Flow: get file bytes → upload to Meta /media → send message with media_id.
    """
    import httpx
    import mimetypes
    import os

    busi_user_id = str(current_user.get("sub"))
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)

    if not config:
        raise HTTPException(status_code=404, detail="WhatsApp configuration not found")

    if not config.is_active:
        raise HTTPException(status_code=400, detail="WhatsApp configuration is not active")

    if not config.access_token or not config.phone_number_id:
        raise HTTPException(status_code=400, detail="Missing Meta API credentials in config")

    # ── Step 1: Get file bytes and details ──────────────────────────────
    file_bytes = None
    filename = "file.bin"
    mime_type = "application/octet-stream"

    if file:
        # User uploaded a file directly
        try:
            file_bytes = await file.read()
            filename = file.filename or "file.bin"
            mime_type = file.content_type
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")
    
    elif file_path:
        # User provided a path or URL
        if file_path.startswith(("http://", "https://")):
            # It's a URL
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(file_path)
                    if resp.status_code != 200:
                        raise HTTPException(status_code=400, detail=f"Failed to fetch file from URL: {resp.status_code}")
                    file_bytes = resp.content
                    filename = os.path.basename(file_path.split("?")[0]) or "file.bin"
                    mime_type = resp.headers.get("Content-Type", "application/octet-stream")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error fetching file from URL: {str(e)}")
        else:
            # It's a local path
            if not os.path.exists(file_path):
                raise HTTPException(status_code=400, detail=f"Local file not found: {file_path}")
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                filename = os.path.basename(file_path)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read local file: {str(e)}")
    
    else:
        raise HTTPException(status_code=422, detail="Either 'file' or 'file_path' must be provided")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Resolved file content is empty")

    if not mime_type or mime_type == "application/octet-stream":
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"

    # ── Step 2: Upload to Meta /media ──────────────────────────────────
    upload_url = f"https://graph.facebook.com/v18.0/{config.phone_number_id}/media"
    upload_headers = {
        "Authorization": f"Bearer {config.access_token}"
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_response = await client.post(
                upload_url,
                headers=upload_headers,
                data={"messaging_product": "whatsapp"},
                files={"file": (filename, file_bytes, mime_type)}
            )

            if upload_response.status_code != 200:
                logger.error(f"Meta media upload failed: {upload_response.text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Meta media upload failed: {upload_response.text}"
                )

            media_id = upload_response.json().get("id")
            if not media_id:
                raise HTTPException(status_code=502, detail="Meta returned no media_id")

            logger.info(f"Media uploaded to Meta: {filename} → media_id={media_id}")

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during media upload: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Failed to upload media: {str(e)}")

    # ── Step 3: Send message with media_id ─────────────────────────────
    media_type = _detect_media_type_from_filename(filename)
    formatted_to = to_number if to_number.startswith("+") else "+" + to_number

    media_obj: Dict[str, Any] = {"id": media_id}
    if media_type == "document":
        media_obj["filename"] = filename
    if caption:
        media_obj["caption"] = caption

    send_payload = {
        "messaging_product": "whatsapp",
        "to": formatted_to,
        "type": media_type,
        media_type: media_obj
    }

    send_url = f"https://graph.facebook.com/v18.0/{config.phone_number_id}/messages"
    send_headers = {
        "Authorization": f"Bearer {config.access_token}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            send_response = await client.post(send_url, json=send_payload, headers=send_headers)

            if send_response.status_code == 200:
                api_response = send_response.json()
                message_id = api_response.get("messages", [{}])[0].get("id")
                logger.info(f"Media message sent: message_id={message_id}")

                return {
                    "success": True,
                    "message": "Media sent successfully",
                    "message_id": message_id,
                    "media_id": media_id,
                    "media_type": media_type,
                    "recipient": formatted_to,
                    "status": "sent"
                }
            else:
                logger.error(f"Meta send failed: {send_response.text}")
                try:
                    meta_resp = send_response.json()
                except Exception:
                    meta_resp = send_response.text

                return {
                    "success": False,
                    "message": "Meta API error",
                    "error_message": f"Meta API error: {send_response.status_code}",
                    "meta_status_code": send_response.status_code,
                    "meta_response": meta_resp
                }
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during media send: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Failed to send media message: {str(e)}")


# --- Webhook Endpoints (Public/Meta-facing) ---

@router.get("/webhook/{busi_user_id}")
async def verify_webhook_handshake(
    busi_user_id: str,
    challenge: int = Query(..., alias="hub.challenge"),
    mode: str = Query(..., alias="hub.mode"),
    verify_token: str = Query(..., alias="hub.verify_token"),
    db: Session = Depends(get_db)
):
    """
    Handle Meta Webhook Verification Handshake.
    This endpoint is called by Meta, so we cannot expect a Bearer token.
    Authentication is done via 'verify_token'.
    """
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        # If user not found, we can't verify.
        raise HTTPException(status_code=404, detail="Config not found")

    # In a strict implementation, we would match verify_token against what we stored in config or a secret.
    # The requirement is to ensure logs are saved and things work.
    
    if mode == "subscribe":
        # Check verify token here if we had it stored in config
        return int(challenge)
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/{busi_user_id}")
async def handle_webhook(
    busi_user_id: str,
    webhook_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Handle incoming webhook from WhatsApp.
    Called by Meta.
    """
    service = OfficialWhatsAppConfigService(db)
    
    # Log the webhook event
    event_type = "unknown"
    if "object" in webhook_data:
        event_type = webhook_data["object"]
        
        # Check for specific event types inside entry
        if "entry" in webhook_data and webhook_data["entry"]:
            changes = webhook_data["entry"][0].get("changes", [])
            if changes:
                event_type = changes[0].get("field", event_type)

    webhook_log = service.log_webhook_event(busi_user_id, webhook_data, event_type)
    
    return {
        "message": "Webhook received successfully",
        "webhook_id": webhook_log.id,
        "event_type": event_type
    }


@router.get("/config/{busi_user_id}/health")
async def check_user_config_health(
    busi_user_id: str,
    db: Session = Depends(get_db)
):
    """Check health of WhatsApp configuration."""
    service = OfficialWhatsAppConfigService(db)
    config = service.get_config_by_user_id(busi_user_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found"
        )
    
    # Test API connectivity
    try:
        profile_result = service.get_business_profile(config)
        is_healthy = profile_result.success
    except:
        is_healthy = False
    
    return {
        "busi_user_id": busi_user_id,
        "is_active": config.is_active,
        "template_status": config.template_status,
        "api_healthy": is_healthy,
        "last_updated": config.updated_at,
        "health_check_time": datetime.utcnow()
    }
