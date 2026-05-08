from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from models.device_session import DeviceSession
from schemas.device_session import DeviceSessionCreate, DeviceSessionUpdate
import uuid

class DeviceSessionService:
    def __init__(self, db: Session):
        self.db = db

    async def invalidate_all_other_sessions(self, device_id: str, exclude_session_id: Optional[str] = None) -> int:
        """Invalidate all active sessions for a device except the current one"""
        query = self.db.query(DeviceSession).filter(
            DeviceSession.device_id == device_id,
            DeviceSession.is_valid == True
        )
        
        if exclude_session_id:
            query = query.filter(DeviceSession.session_id != exclude_session_id)
            
        sessions_to_invalidate = query.all()
        count = len(sessions_to_invalidate)
        
        for session in sessions_to_invalidate:
            session.is_valid = False
            
        self.db.commit()
        return count

    def create_session(self, session_data: DeviceSessionCreate) -> DeviceSession:
        """Create a new device session and invalidate old ones"""
        # First invalidate any existing active sessions for this device
        # We can't use async method here easily without async wrapper, so doing sync logic
        old_sessions = self.db.query(DeviceSession).filter(
            DeviceSession.device_id == session_data.device_id,
            DeviceSession.is_valid == True
        ).all()
        
        for old_session in old_sessions:
            old_session.is_valid = False
            
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        # Ensure timezone-aware datetimes
        created_at = datetime.now(timezone.utc)
        
        db_session = DeviceSession(
            session_id=session_id,
            device_id=session_data.device_id,
            session_token=session_data.session_token,
            expires_at=session_data.expires_at,
            is_valid=True,
            created_at=created_at,
            last_active=created_at
        )
        
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session_by_id(self, session_id: str) -> Optional[DeviceSession]:
        """Get session by ID"""
        return self.db.query(DeviceSession).filter(DeviceSession.session_id == session_id).first()

    def get_session_by_token(self, session_token: str) -> Optional[DeviceSession]:
        """Get session by token"""
        return self.db.query(DeviceSession).filter(DeviceSession.session_token == session_token).first()

    def get_sessions_by_device(
        self, 
        device_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[DeviceSession]:
        """Get sessions for a specific device with pagination"""
        return (
            self.db.query(DeviceSession)
            .filter(DeviceSession.device_id == device_id)
            .order_by(DeviceSession.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_sessions_by_device(self, device_id: str) -> List[DeviceSession]:
        """Get all active sessions for a device"""
        return (
            self.db.query(DeviceSession)
            .filter(
                DeviceSession.device_id == device_id,
                DeviceSession.is_valid == True,
                DeviceSession.expires_at > datetime.now(timezone.utc)
            )
            .all()
        )

    def validate_session(self, session_token: str) -> Optional[DeviceSession]:
        """Validate session and update last active"""
        session = self.get_session_by_token(session_token)
        
        if not session:
            return None
            
        now = datetime.now(timezone.utc)
        
        # Check if expired
        # Ensure session.expires_at is timezone aware if strict comparison is needed, 
        # but usually SQLAlchemy returns TZ-aware if column is TZ-aware.
        if session.expires_at <= now:
            if session.is_valid:
                session.is_valid = False
                self.db.commit()
            return None
            
        # Check if explicitly invalid
        if not session.is_valid:
            return None
            
        # Update last active time 
        # Only update if it's been more than a minute to reduce write load
        if not session.last_active or (now - session.last_active).total_seconds() > 60:
            session.last_active = now
            self.db.commit()
            
        return session

    def extend_session(self, session_id: str, hours: int = 24) -> Optional[DeviceSession]:
        """Extend session expiration"""
        session = self.get_session_by_id(session_id)
        if session and session.is_valid:
            session.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
            session.last_active = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(session)
            return session
        return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        session = self.get_session_by_id(session_id)
        if session:
            session.is_valid = False
            self.db.commit()
            self.db.refresh(session)
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session = self.get_session_by_id(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        now = datetime.now(timezone.utc)
        expired_sessions = (
            self.db.query(DeviceSession)
            .filter(
                (DeviceSession.expires_at <= now) | (DeviceSession.is_valid == False)
            )
            .all()
        )
        
        count = len(expired_sessions)
        for session in expired_sessions:
            self.db.delete(session)
        
        self.db.commit()
        return count

    def get_session_count_by_device(self, device_id: str) -> int:
        """Get total session count for a device"""
        return (
            self.db.query(DeviceSession)
            .filter(DeviceSession.device_id == device_id)
            .count()
        )

    def get_active_session_count_by_device(self, device_id: str) -> int:
        """Get active session count for a device"""
        return (
            self.db.query(DeviceSession)
            .filter(
                DeviceSession.device_id == device_id,
                DeviceSession.is_valid == True,
                DeviceSession.expires_at > datetime.now(timezone.utc)
            )
            .count()
        )
