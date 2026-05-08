import sys
import os
sys.path.append(r"d:\master admin dashboard 2 integration 30-3-2026\whatsapp-api-backend")

from db.session import SessionLocal
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.campaign import Campaign, MessageLog
from models.device import Device
from models.google_sheet import GoogleSheet
from models.message import Message
from sqlalchemy import func

def verify_cascade(user_id_str):
    db = SessionLocal()
    try:
        from uuid import UUID
        user_id = UUID(user_id_str)
        
        print(f"--- Verification for User: {user_id_str} ---")
        
        # 1. Campaigns
        campaign_count = db.query(Campaign).filter(Campaign.busi_user_id == user_id).count()
        print(f"Campaigns: {campaign_count}")
        
        # 2. Devices
        device_count = db.query(Device).filter(Device.busi_user_id == user_id).count()
        print(f"Devices: {device_count}")
        
        # 3. Google Sheets
        sheet_count = db.query(GoogleSheet).filter(GoogleSheet.user_id == user_id).count()
        print(f"Google Sheets: {sheet_count}")
        
        # 4. Messages
        msg_count = db.query(Message).filter(Message.busi_user_id == user_id).count()
        print(f"Messages: {msg_count}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Test with Himanshu Lunge if found
    db = SessionLocal()
    user = db.query(BusiUser).filter(BusiUser.name.like("%Himanshu%")).first()
    if user:
        verify_cascade(str(user.busi_user_id))
    else:
        print("User Himanshu not found.")
    db.close()
