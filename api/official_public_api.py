#!/usr/bin/env python3
"""
Official Public API Routing Layer

Base route: /api/official

Purpose: Expose REST APIs that route requests to Official Message Service.
Only handles requests containing "phone" parameter.

Do NOT:
- Modify database tables
- Implement WhatsApp messaging logic
- Add authentication
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.official_public_message_service import OfficialPublicMessageService
from db.session import get_db
from models.device import Device

logger = logging.getLogger(__name__)

router = APIRouter()


def _normalize_file_path(raw_path: str) -> str:
    if raw_path is None:
        return raw_path

    path = raw_path.strip()

    path = path.replace("\\\\", "\\")

    if ":\\" in path:
        path = path.replace("/", "\\")

    return path


# Request models
class SendMessageRequest(BaseModel):
    phone: str = Field(..., description="Phone number for Official Message Service")
    message: str = Field(..., description="Message content")
    to: str = Field(..., description="Recipient phone number")

class SendFileRequest(BaseModel):
    phone: str = Field(..., description="Phone number for Official Message Service")
    file_path: str = Field(..., description="File path or URL")
    to: str = Field(..., description="Recipient phone number")
    caption: Optional[str] = Field(None, description="Optional caption for the file")

class SendFileTextRequest(BaseModel):
    phone: str = Field(..., description="Phone number for Official Message Service")
    file_path: str = Field(..., description="File path or URL")
    message: str = Field(..., description="Text message")
    to: str = Field(..., description="Recipient phone number")

class SendBase64FileRequest(BaseModel):
    phone: str = Field(..., description="Phone number for Official Message Service")
    base64_data: str = Field(..., description="Base64 encoded file data")
    filename: Optional[str] = Field(None, description="Filename")
    to: str = Field(..., description="Recipient phone number")
    caption: Optional[str] = Field(None, description="Optional caption for the file")


# POST endpoints
@router.post("/send-message")
async def post_send_message(device_id: str = Query(..., description="Device ID"), to: str = Query(..., description="Recipient Phone Number"), message: str = Query(..., description="Message"), db: Session = Depends(get_db)):
    """Send message via Official Message Service using device_id"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_message(
            device_id=device_id,
            phone_number=to,
            message=message
        )
        return {
            "success": True,
            "device_id": device_id,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in POST send-message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-file")
async def post_send_file(
    device_id: str = Query(..., description="Device ID"), 
    to: str = Query(..., description="Recipient Phone Number"), 
    file_path: str = Query(..., description="File path or URL"),
    caption: str = Query(None, description="Optional caption for the file"),
    db: Session = Depends(get_db)
):
    """Send file via Official Message Service using device_id - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")

        import os

        normalized_path = _normalize_file_path(file_path)

        # Check if file exists locally (for ZIP file support)
        if os.path.exists(normalized_path):
            logger.info(f"[OFFICIAL] Local path detected. Raw: {file_path} Normalized: {normalized_path}")
            official_service = OfficialPublicMessageService(db)
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=normalized_path,
                caption=caption
            )
            
            return {
                "success": True,
                "device_id": device_id,
                "file_path": normalized_path,
                "file_url": None,
                "caption": caption,
                "result": result
            }

        if not (normalized_path.startswith("http://") or normalized_path.startswith("https://")):
            raise HTTPException(
                status_code=400,
                detail="Invalid file path. Provide a local path that exists or a public URL starting with http:// or https://"
            )

        file_url = normalized_path
        print("Final public URL:", file_url)
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_media(
            device_id=device_id,
            phone_number=to,
            media_url=file_url
        )
        
        return {
            "success": True,
            "device_id": device_id,
            "file_path": file_path,
            "file_url": file_url,
            "caption": caption,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in POST send-file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-file-text")
async def post_send_file_text(
    device_id: str = Query(..., description="Device ID"), 
    to: str = Query(..., description="Recipient Phone Number"), 
    file_path: str = Query(..., description="File path or URL"), 
    message: str = Query(..., description="Text message"),
    db: Session = Depends(get_db)
):
    """Send file with text via Official Message Service using device_id - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")

        import os
        normalized_path = _normalize_file_path(file_path)

        if os.path.exists(normalized_path):
            logger.info(f"[OFFICIAL] Local path+caption detected. Raw: {file_path} Normalized: {normalized_path}")
            print("Final public URL:", normalized_path)

            official_service = OfficialPublicMessageService(db)
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=normalized_path,
                caption=message
            )

            return {
                "success": True,
                "device_id": device_id,
                "file_path": normalized_path,
                "file_url": None,
                "caption": message,
                "result": result
            }

        if not (normalized_path.startswith("http://") or normalized_path.startswith("https://")):
            raise HTTPException(
                status_code=400,
                detail="Invalid file path. Provide a local path that exists or a public URL starting with http:// or https://"
            )

        print("Final public URL:", normalized_path)

        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_file_with_caption(
            device_id=device_id,
            phone_number=to,
            file_url=normalized_path,
            caption=message
        )
        return {
            "success": True,
            "device_id": device_id,
            "file_path": normalized_path,
            "file_url": normalized_path,
            "caption": message,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in POST send-file-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-base64-file")
async def post_send_base64_file(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    base64_data: str = Query(..., description="Base64 encoded file data"),
    filename: str = Query(..., description="Filename for the file"),
    caption: str = Query(None, description="Optional caption"),
    db: Session = Depends(get_db)
):
    """Send base64 file via Official Message Service using device_id - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        # Convert base64 to dynamically served file
        import base64
        import tempfile
        import os
        import uuid
        import shutil
        
        # Decode base64 data
        try:
            file_data = base64.b64decode(base64_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        safe_filename = f"{unique_id}_{filename.replace(' ', '_')}"
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file to uploads directory
        file_path = os.path.join(uploads_dir, safe_filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Get server base URL dynamically from request
        from fastapi import Request
        # Note: This would require injecting Request into the endpoint
        # For now, use environment variable or default
        import os
        server_host = os.getenv('SERVER_HOST', '127.0.0.1:8000')
        protocol = 'https' if os.getenv('USE_HTTPS', 'false').lower() == 'true' else 'http'
        file_url = f"{protocol}://{server_host}/uploads/{safe_filename}"
        
        logger.info(f"Base64 file processed: {filename} -> {file_url}")
            
        official_service = OfficialPublicMessageService(db)
        
        # Check if it's a ZIP file and handle accordingly
        if filename.lower().endswith('.zip'):
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=file_path,
                caption=caption
            )
        elif caption:
            result = await official_service.send_file_with_caption(
                device_id=device_id,
                phone_number=to,
                file_url=file_url,
                caption=caption
            )
        else:
            result = await official_service.send_media(
                device_id=device_id,
                phone_number=to,
                media_url=file_url
            )
        
        return {
            "success": True,
            "device_id": device_id,
            "filename": filename,
            "file_url": file_url,
            "caption": caption,
            "result": result
        }
            
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-base64-file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoints
@router.get("/send-file-caption")
async def get_send_file_caption(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    file_path: str = Query(..., description="File path or URL"),
    caption: str = Query(..., description="Caption"),
    db: Session = Depends(get_db)
):
    """Send file with caption via Official Message Service (GET) using device_id - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        import os
        normalized_path = _normalize_file_path(file_path)

        # Check if it's a local file
        if os.path.exists(normalized_path):
            logger.info(f"[OFFICIAL] Local path+caption detected in GET. Raw: {file_path} Normalized: {normalized_path}")
            
            official_service = OfficialPublicMessageService(db)
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=normalized_path,
                caption=caption
            )
            
            return {
                "success": True,
                "device_id": device_id,
                "file_path": normalized_path,
                "file_url": None,
                "caption": caption,
                "result": result
            }
        
        # Validate file URL for remote files
        if not (normalized_path.startswith('http://') or normalized_path.startswith('https://')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file path. Provide a local path that exists or a public URL starting with http:// or https://"
            )
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_file_with_caption(
            device_id=device_id,
            phone_number=to,
            file_url=normalized_path,
            caption=caption
        )
        return {
            "success": True,
            "device_id": device_id,
            "file_path": file_path,
            "file_url": normalized_path,
            "caption": caption,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET send-file-caption: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/delivery-report")
async def get_delivery_report(
    device_id: str = Query(..., description="Device ID"),
    message_id: str = Query(..., description="Message ID"),
    db: Session = Depends(get_db)
):
    """Get delivery report via Official Message Service using device_id"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.get_delivery_report(
            device_id=device_id,
            message_id=message_id
        )
        return {
            "success": True,
            "device_id": device_id,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET delivery-report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))







# Additional GET endpoints for message sending
@router.get("/send-message")
async def get_send_message(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    message: str = Query(..., description="Message"),
    db: Session = Depends(get_db)
):
    """Send message via Official Message Service using device_id (GET method)"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_message(
            device_id=device_id,
            phone_number=to,
            message=message
        )
        return {
            "success": True,
            "device_id": device_id,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET send-message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-file")
async def get_send_file(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    file_path: str = Query(..., description="File path or URL"),
    caption: str = Query(None, description="Optional caption for the file"),
    db: Session = Depends(get_db)
):
    """Send file via Official Message Service using device_id (GET method) - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        import os
        normalized_path = _normalize_file_path(file_path)

        # Check if it's a local file
        if os.path.exists(normalized_path):
            logger.info(f"[OFFICIAL] Local path detected in GET. Raw: {file_path} Normalized: {normalized_path}")
            
            official_service = OfficialPublicMessageService(db)
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=normalized_path,
                caption=caption
            )
            
            return {
                "success": True,
                "device_id": device_id,
                "file_path": normalized_path,
                "file_url": None,
                "caption": caption,
                "result": result
            }
        
        # Validate file URL for remote files
        if not (normalized_path.startswith('http://') or normalized_path.startswith('https://')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file path. Provide a local path that exists or a public URL starting with http:// or https://"
            )
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_media(
            device_id=device_id,
            phone_number=to,
            media_url=normalized_path
        )
        return {
            "success": True,
            "device_id": device_id,
            "file_path": file_path,
            "file_url": normalized_path,
            "caption": caption,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET send-file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-file-text")
async def get_send_file_text(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    file_path: str = Query(..., description="File path or URL"),
    message: str = Query(..., description="Text message"),
    db: Session = Depends(get_db)
):
    """Send file with text via Official Message Service using device_id (GET method) - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        import os
        normalized_path = _normalize_file_path(file_path)

        # Check if it's a local file
        if os.path.exists(normalized_path):
            logger.info(f"[OFFICIAL] Local path+caption detected in GET. Raw: {file_path} Normalized: {normalized_path}")
            
            official_service = OfficialPublicMessageService(db)
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=normalized_path,
                caption=message
            )
            
            return {
                "success": True,
                "device_id": device_id,
                "file_path": normalized_path,
                "file_url": None,
                "caption": message,
                "result": result
            }
        
        # Validate file URL for remote files
        if not (normalized_path.startswith('http://') or normalized_path.startswith('https://')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file path. Provide a local path that exists or a public URL starting with http:// or https://"
            )
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_file_with_caption(
            device_id=device_id,
            phone_number=to,
            file_url=normalized_path,
            caption=message
        )
        return {
            "success": True,
            "device_id": device_id,
            "file_path": file_path,
            "file_url": normalized_path,
            "caption": message,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET send-file-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-message-query")
async def get_send_message_query(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    message: str = Query(..., description="Message"),
    db: Session = Depends(get_db)
):
    """Send message via Official Message Service using device_id (Query method)"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_message(
            device_id=device_id,
            phone_number=to,
            message=message
        )
        return {
            "success": True,
            "device_id": device_id,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET send-message-query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-file-query")
async def get_send_file_query(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    file_path: str = Query(..., description="File path or URL"),
    caption: str = Query(None, description="Optional caption for the file"),
    db: Session = Depends(get_db)
):
    """Send file via Official Message Service using device_id (Query method) - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        import os
        normalized_path = _normalize_file_path(file_path)

        # Check if it's a local file
        if os.path.exists(normalized_path):
            logger.info(f"[OFFICIAL] Local path detected in GET query. Raw: {file_path} Normalized: {normalized_path}")
            
            official_service = OfficialPublicMessageService(db)
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=normalized_path,
                caption=caption
            )
            
            return {
                "success": True,
                "device_id": device_id,
                "file_path": normalized_path,
                "file_url": None,
                "caption": caption,
                "result": result
            }
        
        # Validate file URL for remote files
        if not (normalized_path.startswith('http://') or normalized_path.startswith('https://')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file path. Provide a local path that exists or a public URL starting with http:// or https://"
            )
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_media(
            device_id=device_id,
            phone_number=to,
            media_url=normalized_path
        )
        return {
            "success": True,
            "device_id": device_id,
            "file_path": file_path,
            "file_url": normalized_path,
            "caption": caption,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET send-file-query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-message-file-query")
async def get_send_message_file_query(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    file_path: str = Query(..., description="File path or URL"),
    message: str = Query(..., description="Text message"),
    db: Session = Depends(get_db)
):
    """Send file with message via Official Message Service using device_id (Query method) - Supports ZIP files and all media types"""
    try:
        # Get device by ID
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        import os
        normalized_path = _normalize_file_path(file_path)

        # Check if it's a local file
        if os.path.exists(normalized_path):
            logger.info(f"[OFFICIAL] Local path+message detected in GET query. Raw: {file_path} Normalized: {normalized_path}")
            
            official_service = OfficialPublicMessageService(db)
            result = await official_service.send_local_file(
                device_id=device_id,
                phone_number=to,
                file_path=normalized_path,
                caption=message
            )
            
            return {
                "success": True,
                "device_id": device_id,
                "file_path": normalized_path,
                "file_url": None,
                "caption": message,
                "result": result
            }
        
        # Validate file URL for remote files
        if not (normalized_path.startswith('http://') or normalized_path.startswith('https://')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file path. Provide a local path that exists or a public URL starting with http:// or https://"
            )
        
        official_service = OfficialPublicMessageService(db)
        result = await official_service.send_file_with_caption(
            device_id=device_id,
            phone_number=to,
            file_url=normalized_path,
            caption=message
        )
        return {
            "success": True,
            "device_id": device_id,
            "file_path": file_path,
            "file_url": normalized_path,
            "caption": message,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET send-message-file-query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/public/check-config")
async def public_check_config(
    device_id: str = Query(..., description="Device ID"),
    db: Session = Depends(get_db)
):
    """Check if device is actually active via Official Message Service"""
    try:
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            return {
                "success": False,
                "active": False,
                "error": "Device ID not found",
                "message": "Please register your device first"
            }
        
        # Check actual Official Message Service status
        official_service = OfficialPublicMessageService(db)
        
        # Test actual service connectivity and status
        try:
            # Get real business status from Official Message Service
            business_status = await official_service.get_device_status(device_id)
            
            # Determine actual status based on service response
            is_service_active = business_status.get("success", False) if isinstance(business_status, dict) else False
            actual_status = "connected" if is_service_active else "disconnected"
            
            return {
                "success": True,
                "active": device.is_active and is_service_active,
                "device_id": device_id,
                "device_status": actual_status,
                "created_at": device.created_at.isoformat() if device.created_at else None,
                "business_status": business_status
            }
            
        except Exception as service_error:
            return {
                "success": False,
                "active": device.is_active,
                "device_id": device_id,
                "error": "Service check failed",
                "service_error": str(service_error),
                "message": "Unable to verify Official Message Service status"
            }
        
    except Exception as e:
        logger.error(f"Error in public check-config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Template management endpoints
@router.get("/templates")
async def get_templates(
    device_id: str = Query(..., description="Device ID"),
    db: Session = Depends(get_db)
):
    """Get WhatsApp templates for device"""
    try:
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        # Get device configuration directly
        from models.official_whatsapp_config import OfficialWhatsAppConfig
        
        config = db.query(OfficialWhatsAppConfig).filter(
            OfficialWhatsAppConfig.busi_user_id == str(device.busi_user_id),
            OfficialWhatsAppConfig.is_active == True
        ).first()
        
        if not config:
            return {
                "success": False,
                "error": "Device not configured for WhatsApp API",
                "device_id": device_id
            }
        
        logger.info(f"Getting templates for device {device_id}")
        
        import httpx
        
        url = f"https://graph.facebook.com/v18.0/{config.waba_id}/message_templates?fields=name,status,category,language,components"
        headers = {
            "Authorization": f"Bearer {config.access_token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    api_response = response.json()
                    templates = api_response.get("data", [])
                    
                    logger.info(f"Retrieved {len(templates)} templates")
                    
                    return {
                        "success": True,
                        "device_id": device_id,
                        "templates": templates,
                        "total_count": len(templates),
                        "retrieved_at": datetime.now().isoformat()
                    }
                else:
                    error_msg = f"Meta API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "device_id": device_id,
                        "meta_status_code": response.status_code,
                        "meta_response": response.text
                    }
        except Exception as api_error:
            error_msg = f"Failed to call Meta API: {str(api_error)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "device_id": device_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-template")
async def send_template(
    device_id: str = Query(..., description="Device ID"),
    to: str = Query(..., description="Recipient Phone Number"),
    template_name: str = Query(..., description="Template name"),
    language_code: str = Query(..., description="Language code (e.g., en_US)"),
    template_params: str = Query(None, description="Template parameters as JSON string"),
    db: Session = Depends(get_db)
):
    """Send WhatsApp template message"""
    try:
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        # Parse template parameters
        params = []
        if template_params:
            try:
                import json
                params = json.loads(template_params)
            except:
                raise HTTPException(status_code=400, detail="Invalid JSON in template_params")
        
        # Get device configuration directly
        from models.official_whatsapp_config import OfficialWhatsAppConfig
        
        config = db.query(OfficialWhatsAppConfig).filter(
            OfficialWhatsAppConfig.busi_user_id == str(device.busi_user_id),
            OfficialWhatsAppConfig.is_active == True
        ).first()
        
        if not config:
            return {
                "success": False,
                "error": "Device not configured for WhatsApp API",
                "device_id": device_id
            }
        
        logger.info(f"Sending template '{template_name}' to {to}")
        
        import httpx
        
        # Ensure phone number has + prefix for Meta API
        if not to.startswith('+'):
            to = '+' + to
        
        # Build template message payload
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": []
            }
        }
        
        # Add template parameters if provided
        if params:
            for param in params:
                component = {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": param.get("value", "")
                        }
                    ]
                }
                payload["template"]["components"].append(component)
        
        url = f"https://graph.facebook.com/v18.0/{config.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {config.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    api_response = response.json()
                    message_id = api_response.get("messages", [{}])[0].get("id")
                    
                    logger.info(f"Template message sent successfully: {message_id}")
                    
                    return {
                        "success": True,
                        "message_id": message_id,
                        "device_id": device_id,
                        "recipient": to,
                        "template_name": template_name,
                        "language_code": language_code,
                        "template_params": params,
                        "sent_at": datetime.now().isoformat(),
                        "status": "sent"
                    }
                else:
                    error_msg = f"Meta API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "device_id": device_id,
                        "meta_status_code": response.status_code,
                        "meta_response": response.text
                    }
        except Exception as api_error:
            error_msg = f"Failed to call Meta API: {str(api_error)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "device_id": device_id
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Bulk messaging endpoint
@router.post("/bulk-send")
async def bulk_send_messages(
    device_id: str = Query(..., description="Device ID"),
    message: str = Query(..., description="Message to send"),
    recipients: str = Query(..., description="Comma-separated list of phone numbers"),
    db: Session = Depends(get_db)
):
    """Send bulk messages to multiple recipients"""
    try:
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID {device_id} not found or inactive")
        
        # Parse recipients
        recipient_list = [num.strip() for num in recipients.split(',') if num.strip()]
        
        if not recipient_list:
            raise HTTPException(status_code=400, detail="No valid recipients provided")
        
        official_service = OfficialPublicMessageService(db)
        results = []
        
        for recipient in recipient_list:
            try:
                result = await official_service.send_message(
                    device_id=device_id,
                    phone_number=recipient,
                    message=message
                )
                results.append({
                    "recipient": recipient,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "recipient": recipient,
                    "success": False,
                    "error": str(e)
                })
        
        successful_sends = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "device_id": device_id,
            "total_recipients": len(recipient_list),
            "successful_sends": successful_sends,
            "failed_sends": len(recipient_list) - successful_sends,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk_send_messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

