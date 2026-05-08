import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests

# Adjust path to import from backend
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.base import Base
from models.busi_user import BusiUser
from models.device import Device, SessionStatus
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(email: str):
    logger.info(f"Starting cleanup for user email: {email}")
    
    # DB setup
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. Find User
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user:
            logger.error(f"User not found with email: {email}")
            return
            
        logger.info(f"Found User. ID: {user.busi_user_id}")
        
        # 2. Fetch all devices
        devices = db.query(Device).filter(Device.busi_user_id == user.busi_user_id).all()
        logger.info(f"Found {len(devices)} devices linked to this user.")
        
        total_devices_cleaned = 0
        engine_sessions_deleted = 0
        
        for device in devices:
            device_id_str = str(device.device_id)
            logger.info(f"Cleaning Device: {device_id_str} ({device.device_name})")
            
            # Update DB
            device.session_status = SessionStatus.logged_out
            device.is_active = False
            device.qr_code = None
            
            # Delete from Engine
            try:
                engine_url = f"{settings.WHATSAPP_ENGINE_BASE_URL}/session/{device_id_str}/logout"
                response = requests.delete(engine_url, timeout=2) # Reduced timeout
                if response.status_code in (200, 404):
                    logger.info(f"  engine session deleted/not found for {device_id_str}")
                    engine_sessions_deleted += 1
                else:
                    logger.warning(f"  Failed to delete engine session: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"  Engine unreachable or timed out for {device_id_str}: {e}. Proceeding with DB cleanup.")
            except Exception as e:
                logger.error(f"  Error communicating with engine for {device_id_str}: {e}")
                
            total_devices_cleaned += 1
            
        db.commit()
        
        logger.info("Cleanup completed successfully.")
        result = {
            "total_devices_cleaned": total_devices_cleaned,
            "engine_sessions_deleted": engine_sessions_deleted,
            "success": True
        }
        print(f"\nRESULT: {result}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup_user_devices.py <email>")
        sys.exit(1)
    
    main(sys.argv[1])
