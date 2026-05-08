#!/usr/bin/env python3
"""
Unofficial Public API Routing Layer

Base route: /api/unofficial

Purpose: Expose REST APIs that route requests to WhatsApp Engine Service.
Only handles requests containing "id" and "name" parameters.

Do NOT:
- Modify database tables
- Implement WhatsApp messaging logic
- Add authentication
"""

import logging
import time
import os
import tempfile
import uuid
import shutil
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, Body, Depends, Form, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.whatsapp_engine_service import WhatsAppEngineService
from db.session import get_db
from api.auth import get_current_user
from core.plan_validator import check_busi_user_plan
from models.busi_user import BusiUser

logger = logging.getLogger(__name__)

router = APIRouter()


def _normalize_unofficial_file_path(file_path: str) -> str:
    if not file_path:
        return file_path
    
    # Strip literal quotes that users might copy-paste
    file_path = file_path.strip().strip("'").strip('"')
    
    if file_path.startswith(("http://", "https://")):
        return file_path
        
    file_path = file_path.replace("\\\\", "\\")
    return os.path.abspath(file_path)

async def _deferred_cleanup(file_path: str, delay: int = 10):
    """Wait and then delete a temporary file"""
    try:
        import asyncio
        await asyncio.sleep(delay)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Deferred cleanup: Removed {file_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed deferred cleanup for {file_path}: {e}")

def _handle_engine_result(result: Dict[str, Any], default_error: str = "Engine operation failed"):
    """Check engine result and raise HTTPException if failed"""
    if not result or not result.get("success"):
        msg = result.get("message", default_error) if result else default_error
        err_code = result.get("error_code") if result else None
        
        status_code = 400
        # If it looks like a network/gateway error, use 502
        if any(term in msg for term in ["Bad Gateway", "Service Unavailable", "no response", "timeout", "Connection"]):
            status_code = 502
            
        # Return structured detail so frontend can parse error_code
        raise HTTPException(
            status_code=status_code, 
            detail={"message": msg, "error_code": err_code}
        )
    return result

# Request models
class SendMessageRequest(BaseModel):
    device_id: str = Field(..., description="Device ID for WhatsApp Engine Service")
    device_name: str = Field(..., description="Device name for WhatsApp Engine Service")
    receiver_number: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="Message content")
    wait_for_delivery: bool = Field(False, description="Wait for real-time delivery confirmation")
    max_wait_time: int = Field(30, description="Maximum time to wait for delivery (seconds)")

class SendFileRequest(BaseModel):
    device_id: str = Field(..., description="Device ID for WhatsApp Engine Service")
    device_name: str = Field(..., description="Device name for WhatsApp Engine Service")
    receiver_number: str = Field(..., description="Recipient phone number")
    file_path: str = Field(..., description="File path or URL")

class SendFileTextRequest(BaseModel):
    device_id: str = Field(..., description="Device ID for WhatsApp Engine Service")
    device_name: str = Field(..., description="Device name for WhatsApp Engine Service")
    receiver_number: str = Field(..., description="Recipient phone number")
    file_path: str = Field(..., description="File path or URL")
    message: str = Field(..., description="Text message")

class SendBase64FileRequest(BaseModel):
    device_id: str = Field(..., description="Device ID for WhatsApp Engine Service")
    device_name: str = Field(..., description="Device name for WhatsApp Engine Service")
    receiver_number: str = Field(..., description="Recipient phone number")
    base64_data: str = Field(..., description="Base64 encoded file data")
    filename: Optional[str] = Field(None, description="Filename")

class ContactItem(BaseModel):
    name: str = Field(..., description="Contact name")
    phone: str = Field(..., description="Contact phone number")

class AddContactsRequest(BaseModel):
    contacts: List[ContactItem] = Field(..., description="List of contacts to add")

# POST endpoints
@router.post("/send-message")
def post_send_message(
    request: SendMessageRequest, 
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send message via WhatsApp Engine Service with optional real-time delivery tracking"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    try:
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_text(
            device_id=request.device_id,
            to=request.receiver_number,
            message=request.message,
            device_name=request.device_name,
            wait_for_delivery=request.wait_for_delivery,
            max_wait_time=request.max_wait_time,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return _handle_engine_result(result, "Failed to send message")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-file")
def post_send_file(
    background_tasks: BackgroundTasks,
    device_id: str = Form(...),
    device_name: str = Form(...),
    receiver_number: str = Form(...),
    file_path: str = Form(""),
    file: Optional[UploadFile] = File(None),
    wait_for_delivery: bool = Form(True),
    max_wait_time: int = Form(30),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send file via WhatsApp Engine Service (accepts path or upload)"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    temp_path = None
    try:
        if file:
            # Handle direct file upload
            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            os.makedirs("temp_uploads", exist_ok=True)
            temp_path = os.path.abspath(os.path.join("temp_uploads", temp_filename))
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_path = temp_path
            # Schedule cleanup
            background_tasks.add_task(_deferred_cleanup, temp_path)

        normalized_file_path = _normalize_unofficial_file_path(file_path)
        logger.info(f"[SEND-FILE] device_id={device_id}, device_name={device_name}, receiver={receiver_number}")
        logger.info(f"[SEND-FILE] file_path={normalized_file_path}")
        
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_file(
            device_id=device_id,
            to=receiver_number,
            file_path=normalized_file_path,
            device_name=device_name,
            wait_for_delivery=wait_for_delivery,
            max_wait_time=max_wait_time,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return _handle_engine_result(result, "Failed to send file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-file-text")
def post_send_file_text(
    background_tasks: BackgroundTasks,
    device_id: str = Form(...),
    device_name: str = Form(...),
    receiver_number: str = Form(...),
    file_path: str = Form(""),
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    wait_for_delivery: bool = Form(True),
    max_wait_time: int = Form(30),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send file with text via WhatsApp Engine Service (accepts path or upload)"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    temp_path = None
    try:
        if file:
            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            os.makedirs("temp_uploads", exist_ok=True)
            temp_path = os.path.abspath(os.path.join("temp_uploads", temp_filename))
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_path = temp_path
            background_tasks.add_task(_deferred_cleanup, temp_path)

        normalized_file_path = _normalize_unofficial_file_path(file_path)
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_file_with_caption(
            device_id=device_id,
            to=receiver_number,
            file_path=normalized_file_path,
            caption=message,
            device_name=device_name
        )
        return _handle_engine_result(result, "Failed to send file with text")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-file-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-base64-file")
def post_send_base64_file(
    device_id: str = Form(...),
    device_name: str = Form(...),
    receiver_number: str = Form(...),
    base64_data: str = Form(...),
    filename: str = Form(""),
    wait_for_delivery: bool = Form(True),
    max_wait_time: int = Form(30),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send base64 file via WhatsApp Engine Service (form data only)"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    try:
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_base64_file(
            device_id=device_id,
            to=receiver_number,
            base64_data=base64_data,
            filename=filename,
            device_name=device_name,
            wait_for_delivery=wait_for_delivery,
            max_wait_time=max_wait_time,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return _handle_engine_result(result, "Failed to send base64 file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-base64-file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-file")
def get_send_file(
    device_id: str = Query(...),
    device_name: str = Query(...),
    receiver_number: str = Query(...),
    file_path: str = Query(...),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send file via WhatsApp Engine Service (GET)"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    try:
        normalized_file_path = _normalize_unofficial_file_path(file_path)
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_file(
            device_id=device_id,
            to=receiver_number,
            file_path=normalized_file_path,
            device_name=device_name,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return result
    except Exception as e:
        logger.error(f"Error in GET send-file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-file-text")
def get_send_file_text(
    device_id: str = Query(...),
    device_name: str = Query(...),
    receiver_number: str = Query(...),
    file_path: str = Query(...),
    message: str = Query(...),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send file with text via WhatsApp Engine Service (GET)"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    try:
        normalized_file_path = _normalize_unofficial_file_path(file_path)
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_file_with_caption(
            device_id=device_id,
            to=receiver_number,
            file_path=normalized_file_path,
            caption=message,
            device_name=device_name,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return result
    except Exception as e:
        logger.error(f"Error in GET send-file-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-file-caption")
def post_send_file_caption(
    background_tasks: BackgroundTasks,
    device_id: str = Form(...),
    device_name: str = Form(...),
    receiver_number: str = Form(...),
    file_path: str = Form(""),
    caption: str = Form(...),
    file: Optional[UploadFile] = File(None),
    wait_for_delivery: bool = Form(True),
    max_wait_time: int = Form(30),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send file with caption via WhatsApp Engine Service (accepts path or upload)"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    temp_path = None
    try:
        if file:
            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            os.makedirs("temp_uploads", exist_ok=True)
            temp_path = os.path.abspath(os.path.join("temp_uploads", temp_filename))
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_path = temp_path
            background_tasks.add_task(_deferred_cleanup, temp_path)

        normalized_file_path = _normalize_unofficial_file_path(file_path)
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_file_with_caption(
            device_id=device_id,
            to=receiver_number,
            file_path=normalized_file_path,
            caption=caption,
            device_name=device_name,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-file-caption: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/send-file-caption")
def get_send_file_caption(
    device_id: str = Query(...),
    device_name: str = Query(...),
    receiver_number: str = Query(...),
    file_path: str = Query(...),
    caption: str = Query(...),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send file with caption via WhatsApp Engine Service (GET)"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    try:
        normalized_file_path = _normalize_unofficial_file_path(file_path)
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_file_with_caption(
            device_id=device_id,
            to=receiver_number,
            file_path=normalized_file_path,
            caption=caption,
            device_name=device_name,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return result
    except Exception as e:
        logger.error(f"Error in GET send-file-caption: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Query endpoints
@router.get("/send-message-query")
def get_send_message_query(
    device_id: str = Query(...),
    device_name: str = Query(...),
    receiver_number: str = Query(...),
    message: str = Query(...),
    wait_for_delivery: bool = Query(False, description="Wait for real-time delivery confirmation"),
    max_wait_time: int = Query(30, description="Maximum time to wait for delivery (seconds)"),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send message via query parameters with optional real-time delivery tracking"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    try:
        engine_service = WhatsAppEngineService(db)
        result = engine_service.send_text(
            device_id=device_id,
            to=receiver_number,
            message=message,
            device_name=device_name,
            wait_for_delivery=wait_for_delivery,
            max_wait_time=max_wait_time,
            authenticated_user_id=str(current_user.busi_user_id)
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-message-query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-file-query")
def get_send_file_query(
    device_id: str = Query(...),
    device_name: str = Query(...),
    receiver_number: str = Query(...),
    file_path: str = Query(...)
):
    """Send file via query parameters"""
    return get_send_file(device_id, device_name, receiver_number, file_path)




class MessageItem(BaseModel):
    number: str
    message: str

class BulkSendMessagesRequest(BaseModel):
    id: str  # maps to device_id
    name: str # maps to device_name
    messages: List[MessageItem]
    wait_for_delivery: bool = True
    max_wait_time: int = 30

# Bulk API endpoints
@router.post("/bulk-send-messages")
async def bulk_send_messages(
    request: BulkSendMessagesRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send bulk messages with real-time delivery tracking using JSON payload"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    try:
        engine_service = WhatsAppEngineService(db)
        results = []
        
        logger.info(f"Starting bulk message send: {len(request.messages)} recipients")
        logger.info(f"Wait for delivery: {request.wait_for_delivery}, Max wait time: {request.max_wait_time}")
        
        for i, item in enumerate(request.messages):
            recipient = item.number.strip()
            message_text = item.message
            
            logger.info(f"Processing message {i+1}/{len(request.messages)} to {recipient}")
            
            try:
                # Validate phone number format before sending
                from utils.validators import validate_phone
                if not validate_phone(recipient):
                    results.append({
                        "recipient": recipient,
                        "message": message_text,
                        "status": "error",
                        "error": "Invalid phone number format (must be 10-15 digits)",
                        "index": i + 1
                    })
                    logger.error(f"Message {i+1} failed to {recipient}: Invalid phone number format")
                    continue
                
                result = engine_service.send_text(
                    device_id=request.id,
                    to=recipient,
                    message=message_text,
                    device_name=request.name,
                    wait_for_delivery=request.wait_for_delivery,
                    max_wait_time=request.max_wait_time,
                    skip_credit_deduction=True,  # Skip per-message deduction, will deduct after loop
                    authenticated_user_id=str(current_user.busi_user_id)
                )
                
                # Check if the send was actually successful
                if result and result.get("success"):
                    results.append({
                        "recipient": recipient,
                        "message": message_text,
                        "status": "success",
                        "result": result,
                        "index": i + 1
                    })
                    
                    # Check if delivery was confirmed
                    if request.wait_for_delivery and result.get("result", {}).get("delivery_tracking", {}).get("delivered"):
                        logger.info(f"Message {i+1} delivery confirmed for {recipient}")
                    elif request.wait_for_delivery:
                        delivery_status = result.get("result", {}).get("delivery_tracking", {}).get("status", "unknown")
                        logger.info(f"Message {i+1} delivery status for {recipient}: {delivery_status}")
                    
                    logger.info(f"Message {i+1} sent successfully to {recipient}")
                else:
                    # Check for non-WhatsApp registration errors
                    error_msg = result.get("error", "Unknown error") if result else "No response from engine"
                    if result:
                        error_msg_lower = error_msg.lower()
                        if "not on whatsapp" in error_msg_lower or "not registered" in error_msg_lower:
                            error_msg = "Number not registered on WhatsApp"
                        elif "invalid" in error_msg_lower and "phone" in error_msg_lower:
                            error_msg = "Invalid phone number"
                    
                    error_result = {
                        "recipient": recipient,
                        "message": message_text,
                        "status": "error",
                        "error": error_msg,
                        "index": i + 1
                    }
                    results.append(error_result)
                    logger.error(f"Message {i+1} failed to {recipient}: {error_msg}")
                
            except Exception as e:
                error_result = {
                    "recipient": recipient,
                    "message": message_text,
                    "status": "error",
                    "error": str(e),
                    "index": i + 1
                }
                results.append(error_result)
                logger.error(f"Message {i+1} failed to {recipient}: {str(e)}")
        
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = sum(1 for r in results if r["status"] == "error")
        delivered_count = sum(1 for r in results if r.get("result", {}).get("delivery_tracking", {}).get("delivered", False))
        
        logger.info(f"Bulk message send completed: {success_count} success, {error_count} errors, {delivered_count} delivered")
        
        # 🔥 DEDUCT CREDITS AFTER LOOP (only for successful messages)
        if success_count > 0:
            try:
                from services.message_usage_service import MessageUsageService
                message_usage_service = MessageUsageService(db)
                
                # Deduct credits for all successful messages at once
                message_usage_service.deduct_credits(
                    busi_user_id=str(current_user.busi_user_id),
                    message_id=f"bulk-{uuid.uuid4().hex[:8]}",
                    amount=success_count,
                    source="bulk"
                )
                db.commit()
                logger.info(f"✅ Deducted {success_count} credits for bulk flow (source: bulk)")
            except Exception as credit_err:
                logger.error(f"⚠️ Credit deduction failed after bulk send: {str(credit_err)}")
        
        return {
            "success": True,
            "total_recipients": len(request.messages),
            "success_count": success_count,
            "error_count": error_count,
            "delivered_count": delivered_count,
            "results": results,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error in bulk-send-messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-send-files")
async def bulk_send_files(
    background_tasks: BackgroundTasks,
    device_id: str = Form(...),
    device_name: str = Form(...),
    recipients: Optional[List[str]] = Form(None),
    recipients_raw: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send bulk files with real-time delivery tracking using proper multipart/form-data"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    # Validate device
    if not device_id or not device_name:
        raise HTTPException(status_code=400, detail="Device info required")

    # Normalize recipients
    if recipients:
        final_recipients = recipients
    elif recipients_raw:
        final_recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    else:
        raise HTTPException(status_code=400, detail="Recipients required")
        
    if not final_recipients:
        raise HTTPException(status_code=400, detail="At least one recipient required")

    # Decide file source
    temp_file_path = None

    try:
        if file:
            # Save uploaded file temporarily
            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            os.makedirs("temp_uploads", exist_ok=True)
            temp_file_path = os.path.abspath(os.path.join("temp_uploads", temp_filename))

            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            send_path = temp_file_path
            background_tasks.add_task(_deferred_cleanup, temp_file_path)

        elif file_path:
            send_path = file_path

        else:
            raise HTTPException(status_code=400, detail="File or file_path required")
            
        engine_service = WhatsAppEngineService(db)
        results = []
        
        logger.info(f"Starting bulk file send: {len(final_recipients)} recipients")
        
        normalized_file_path = _normalize_unofficial_file_path(send_path)
        file_name_for_log = file_path if file_path else getattr(file, "filename", "unknown")
            
        for i, recipient in enumerate(final_recipients):
            logger.info(f"Processing file {i+1}/{len(final_recipients)} to {recipient}")

            try:
                # Validate phone number format before sending
                from utils.validators import validate_phone
                if not validate_phone(recipient):
                    results.append({
                        "recipient": recipient,
                        "file_path": file_name_for_log,
                        "status": "error",
                        "error": "Invalid phone number format (must be 10-15 digits)",
                        "index": i + 1
                    })
                    logger.error(f"File {i+1} failed to {recipient}: Invalid phone number format")
                    continue

                result = engine_service.send_file(
                    device_id=device_id,
                    to=recipient,
                    file_path=normalized_file_path,
                    device_name=device_name
                )
                
                if not result.get("success"):
                    raise Exception(result.get("error") or result.get("message") or "Unknown error from engine")
                
                results.append({
                    "recipient": recipient,
                    "file_path": file_name_for_log,
                    "status": "success",
                    "result": result,
                    "index": i + 1
                })
                
                logger.info(f"File {i+1} sent successfully to {recipient}")
                
            except Exception as e:
                error_result = {
                    "recipient": recipient,
                    "file_path": file_name_for_log,
                    "status": "error",
                    "error": str(e),
                    "index": i + 1
                }
                results.append(error_result)
                logger.error(f"File {i+1} failed to {recipient}: {str(e)}")
        
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = sum(1 for r in results if r["status"] == "error")
        delivered_count = sum(1 for r in results if r.get("result", {}).get("delivery_tracking", {}).get("delivered", False))
        
        logger.info(f"Bulk file send completed: {success_count} success, {error_count} errors, {delivered_count} delivered")
        
        return {
            "success": True,
            "total_recipients": len(final_recipients),
            "success_count": success_count,
            "error_count": error_count,
            "delivered_count": delivered_count,
            "results": results,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk-send-files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/bulk-send-files-with-text")
async def bulk_send_files_with_text(
    background_tasks: BackgroundTasks,
    device_id: str = Form(...),
    device_name: str = Form(...),
    text: str = Form(...),
    recipients: Optional[List[str]] = Form(None),
    recipients_raw: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: BusiUser = Depends(get_current_user)
):
    """Send bulk files with text using proper multipart/form-data"""
    # 🔐 Enforce Plan Validation
    if current_user.role in ["user", "business_owner"]:
        check_busi_user_plan(db, str(current_user.busi_user_id))

    # Validate device
    if not device_id or not device_name:
        raise HTTPException(status_code=400, detail="Device info required")

    # Normalize recipients
    if recipients:
        final_recipients = recipients
    elif recipients_raw:
        final_recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    else:
        raise HTTPException(status_code=400, detail="Recipients required")
        
    if not final_recipients:
        raise HTTPException(status_code=400, detail="At least one recipient required")

    # Decide file source
    temp_file_path = None

    if file:
        # Save uploaded file temporarily
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        os.makedirs("temp_uploads", exist_ok=True)
        temp_file_path = os.path.abspath(os.path.join("temp_uploads", temp_filename))

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        send_path = temp_file_path
        background_tasks.add_task(_deferred_cleanup, temp_file_path, 60) # Long delay for bulk text

    elif file_path:
        # Check if it's a URL or a local path
        if not file_path.startswith(("http://", "https://")):
            # Standardize path (remove quotes, handle backslashes)
            norm_p = _normalize_unofficial_file_path(file_path)
            
            # If it's a Windows-style path being passed to a Linux server, it won't exist
            if not os.path.exists(norm_p):
                # Extra check: maybe it's relative?
                if not os.path.isabs(norm_p):
                    abs_p = os.path.abspath(norm_p)
                    if os.path.exists(abs_p):
                        send_path = abs_p
                    else:
                        raise HTTPException(status_code=400, detail=f"File not found on server: {file_path}")
                else:
                    raise HTTPException(status_code=400, detail=f"File not found on server: {file_path}")
            else:
                send_path = norm_p
        else:
            send_path = file_path
    else:
        raise HTTPException(status_code=400, detail="File or file_path (URL) required")
        
    try:
        engine_service = WhatsAppEngineService(db)
        results = []
        
        logger.info(f"Starting bulk file+text send: {len(final_recipients)} recipients")
        
        normalized_file_path = _normalize_unofficial_file_path(send_path)
        file_name_for_log = file_path if file_path else getattr(file, "filename", "unknown")
            
        for i, recipient in enumerate(final_recipients):
            logger.info(f"Processing item {i+1}/{len(final_recipients)} to {recipient}")

            try:
                # Validate phone number format before sending
                from utils.validators import validate_phone
                if not validate_phone(recipient):
                    results.append({
                        "recipient": recipient,
                        "file_path": file_name_for_log,
                        "message": text,
                        "status": "error",
                        "error": "Invalid phone number format (must be 10-15 digits)",
                        "index": i + 1
                    })
                    logger.error(f"Item {i+1} failed to {recipient}: Invalid phone number format")
                    continue

                # Send file with caption
                result = engine_service.send_file_with_caption(
                    device_id=device_id,
                    to=recipient,
                    file_path=normalized_file_path,
                    caption=text,
                    device_name=device_name
                )

                # Check if the send was actually successful
                if result and result.get("success"):
                    results.append({
                        "recipient": recipient,
                        "file_path": file_name_for_log,
                        "message": text,
                        "status": "success",
                        "result": result,
                        "index": i + 1
                    })

                    logger.info(f"File+text {i+1} sent successfully to {recipient}")
                else:
                    # Check for non-WhatsApp registration errors
                    error_msg = result.get("error", "Unknown error") if result else "No response from engine"
                    if result:
                        error_msg_lower = error_msg.lower()
                        if "not on whatsapp" in error_msg_lower or "not registered" in error_msg_lower:
                            error_msg = "Number not registered on WhatsApp"
                        elif "invalid" in error_msg_lower and "phone" in error_msg_lower:
                            error_msg = "Invalid phone number"

                    error_result = {
                        "recipient": recipient,
                        "message": text,
                        "status": "error",
                        "error": error_msg,
                        "index": i + 1,
                        "file_path": file_name_for_log
                    }
                    results.append(error_result)
                    logger.error(f"Item {i+1} failed to {recipient}: {error_msg}")

            except Exception as e:
                error_result = {
                    "recipient": recipient,
                    "message": text,
                    "status": "error",
                    "error": str(e),
                    "index": i + 1,
                    "file_path": file_name_for_log
                }
                results.append(error_result)
                logger.error(f"Item {i+1} failed to {recipient}: {str(e)}")
        
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = sum(1 for r in results if r["status"] == "error")
        delivered_count = sum(1 for r in results if r.get("result", {}).get("delivery_tracking", {}).get("delivered", False))
        
        operation_type = "file+text"
        logger.info(f"Bulk {operation_type} send completed: {success_count} success, {error_count} errors, {delivered_count} delivered")
        
        return {
            "success": True,
            "operation_type": operation_type,
            "total_recipients": len(final_recipients),
            "success_count": success_count,
            "error_count": error_count,
            "delivered_count": delivered_count,
            "results": results,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk-send-files-with-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/delivery-report")
async def get_delivery_report(
    device_id: str = Query(...),
    device_name: str = Query(...),
    message_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Get delivery report via WhatsApp Engine Service"""
    try:
        engine_service = WhatsAppEngineService(db)
        result = engine_service.check_message_status(device_id, message_id)
        return result
    except Exception as e:
        logger.error(f"Error in delivery-report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status-check")
def status_check(
    device_id: str = Query(...),
    device_name: str = Query(...),
    db: Session = Depends(get_db)
):
    """Check service status via WhatsApp Engine Service"""
    try:
        engine_service = WhatsAppEngineService(db)
        result = engine_service.status_check(device_id=device_id)
        return result
    except Exception as e:
        logger.error(f"Error in status-check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))