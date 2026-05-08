import sys
import logging
from uuid import UUID
from sqlalchemy.orm import Session
from db.base import SessionLocal
from services.official_whatsapp_config_service import OfficialWhatsAppConfigService
from schemas.official_whatsapp_config import OfficialWhatsAppConfigCreate, WhatsAppOfficialConfig, OfficialWhatsAppConfigUpdate

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User Config
BUSI_USER_ID = "d1bc821d-9297-486c-9484-6ec4dd05cb54"
BUSINESS_NUMBER = "91452910501"
WABA_ID = "835555522815714"
PHONE_NUMBER_ID = "970142222843511"
ACCESS_TOKEN = "EAAMRWt4FwdgBQWDfgR7CiP3O4KI2qjGaL8JUFioYMKurRjw7gQWUKwLZAbydI8gbv8d2TsdX40fYjDvUEalcfIZAWt4tjZC3uuB0p1ZBZBDVQfXeyOomsNM3ZAXx9tuzjhHdhgCGlleHvTZCVX6QocP2w5BGNb2vqbCTeOOHig7id0tZCDwuNCKtxAU3k91hioqQS7WxSZAsisR0Wzq1lmYrjCRZCTqQZBiHQodhKs80hlEIVlTsZAx4Wu0hUMH8KWQwu874zmuvxlX7lHnXScRFqt79"

def setup_config():
    db = SessionLocal()
    service = OfficialWhatsAppConfigService(db)
    
    try:
        logger.info(f"Checking config for user: {BUSI_USER_ID}")
        existing_config = service.get_config_by_user_id(BUSI_USER_ID)
        
        wa_config = WhatsAppOfficialConfig(
            business_number=BUSINESS_NUMBER,
            waba_id=WABA_ID,
            phone_number_id=PHONE_NUMBER_ID,
            access_token=ACCESS_TOKEN,
            template_status="pending"
        )

        if existing_config:
            logger.info("Config exists. Updating...")
            update_data = OfficialWhatsAppConfigUpdate(
                whatsapp_official=wa_config,
                is_active=True
            )
            updated = service.update_config(BUSI_USER_ID, update_data)
            logger.info("Config updated successfully!")
            logger.info(f"ID: {updated.id}, Active: {updated.is_active}")
        else:
            logger.info("Config not found. Creating...")
            create_data = OfficialWhatsAppConfigCreate(
                busi_user_id=BUSI_USER_ID,
                whatsapp_official=wa_config
            )
            created = service.create_config(create_data)
            logger.info("Config created successfully!")
            logger.info(f"ID: {created.id}, Active: {created.is_active}")

        # Verification: Sync templates
        logger.info("Attempting to sync templates...")
        config = service.get_config_by_user_id(BUSI_USER_ID)
        sync_result = service.sync_templates(config)
        logger.info(f"Sync Result: {sync_result.message}")
        
        if sync_result.success:
            logger.info("Templates synced successfully!")
        else:
            logger.error(f"Template sync failed: {sync_result.error_message}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    setup_config()
