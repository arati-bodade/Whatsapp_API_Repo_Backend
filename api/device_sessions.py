from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.session import get_db
from services.device_session_service import DeviceSessionService
from schemas.device_session import (
    DeviceSessionCreate, 
    DeviceSessionResponse, 
    DeviceSessionListResponse,
    DeviceSessionValidateRequest,
    DeviceSessionValidateResponse,
    DeviceSessionExtendRequest,
    DeviceSessionExtendResponse
)
from datetime import datetime, timedelta
from typing import List


router = APIRouter(prefix="/device-sessions", tags=["Device Sessions"])


def get_device_session_service(db: Session = Depends(get_db)) -> DeviceSessionService:
    return DeviceSessionService(db)


@router.post("/", response_model=DeviceSessionResponse)
async def create_session(
    session_data: DeviceSessionCreate,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Create a new device session"""
    try:
        session = session_service.create_session(session_data)
        return DeviceSessionResponse(
            session_id=session.session_id,
            device_id=session.device_id,
            session_token=session.session_token,
            is_valid=session.is_valid,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_active=session.last_active
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/{session_id}", response_model=DeviceSessionResponse)
async def get_session(
    session_id: str,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Get session by ID"""
    session = session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return DeviceSessionResponse(
        session_id=session.session_id,
        device_id=session.device_id,
        session_token=session.session_token,
        is_valid=session.is_valid,
        created_at=session.created_at,
        expires_at=session.expires_at,
        last_active=session.last_active
    )


@router.get("/device/{device_id}", response_model=DeviceSessionListResponse)
async def get_sessions_by_device(
    device_id: str,
    page: int = 1,
    size: int = 20,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Get all sessions for a device with pagination"""
    skip = (page - 1) * size
    sessions = session_service.get_sessions_by_device(device_id, skip=skip, limit=size)
    total = session_service.get_session_count_by_device(device_id)
    
    session_responses = [
        DeviceSessionResponse(
            session_id=session.session_id,
            device_id=session.device_id,
            session_token=session.session_token,
            is_valid=session.is_valid,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_active=session.last_active
        )
        for session in sessions
    ]
    
    return DeviceSessionListResponse(
        sessions=session_responses,
        total=total,
        page=page,
        size=size
    )


@router.get("/device/{device_id}/active", response_model=List[DeviceSessionResponse])
async def get_active_sessions_by_device(
    device_id: str,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Get all active sessions for a device"""
    sessions = session_service.get_active_sessions_by_device(device_id)
    
    return [
        DeviceSessionResponse(
            session_id=session.session_id,
            device_id=session.device_id,
            session_token=session.session_token,
            is_valid=session.is_valid,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_active=session.last_active
        )
        for session in sessions
    ]


@router.post("/validate", response_model=DeviceSessionValidateResponse)
async def validate_session(
    validate_request: DeviceSessionValidateRequest,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Validate session token"""
    session = session_service.validate_session(validate_request.session_token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return DeviceSessionValidateResponse(
        session_id=session.session_id,
        device_id=session.device_id,
        is_valid=session.is_valid,
        expires_at=session.expires_at
    )


@router.post("/extend", response_model=DeviceSessionExtendResponse)
async def extend_session(
    extend_request: DeviceSessionExtendRequest,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Extend session expiration"""
    session = session_service.extend_session(extend_request.session_id, extend_request.hours)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or invalid")
    
    return DeviceSessionExtendResponse(
        session_id=session.session_id,
        expires_at=session.expires_at,
        message=f"Session extended by {extend_request.hours} hours"
    )


@router.patch("/{session_id}/invalidate")
async def invalidate_session(
    session_id: str,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Invalidate a session"""
    success = session_service.invalidate_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session invalidated successfully"}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Delete a session"""
    success = session_service.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}


@router.post("/cleanup/expired")
async def cleanup_expired_sessions(
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Clean up expired sessions"""
    count = session_service.cleanup_expired_sessions()
    
    return {"message": f"Cleaned up {count} expired sessions"}


@router.get("/device/{device_id}/stats")
async def get_device_session_stats(
    device_id: str,
    session_service: DeviceSessionService = Depends(get_device_session_service)
):
    """Get session statistics for a device"""
    total_sessions = session_service.get_session_count_by_device(device_id)
    active_sessions = session_service.get_active_session_count_by_device(device_id)
    
    return {
        "device_id": device_id,
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "expired_sessions": total_sessions - active_sessions
    }
