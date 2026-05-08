import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from db.session import get_db
from models.busi_user import BusiUser
from core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user_ws(token: str, db: Session) -> Optional[BusiUser]:
    """
    Authenticate user for WebSocket connections using JWT token.
    Similar to get_current_user but adapted for WebSocket auth.
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("WebSocket token missing user_id")
            return None
        
        # Get user from database
        user = db.query(BusiUser).filter(BusiUser.busi_user_id == user_id).first()
        if user is None:
            logger.warning(f"WebSocket auth failed: User {user_id} not found")
            return None
        
        return user
        
    except JWTError as e:
        logger.warning(f"WebSocket JWT error: {e}")
        return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None
