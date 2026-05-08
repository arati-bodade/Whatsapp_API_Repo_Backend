import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from db.session import get_db
from models.whatsapp_inbox import WhatsAppInbox
from models.device import Device
import datetime

def check_messages():
    db = next(get_db())
    user_id = "2b2cce47-d16f-4242-b76d-69a9170e5e73"
    
    print(f"--- DEBUG INFO FOR USER: {user_id} ---")
    
    # 1. List all web devices for this user
    from models.device import DeviceType
    devices = db.query(Device).filter(
        Device.busi_user_id == user_id,
        Device.device_type == DeviceType.web
    ).all()
    
    device_ids = [d.device_id for d in devices]
    print(f"Web devices found: {len(devices)}")
    for d in devices:
        print(f"  ID: {d.device_id}, Name: {d.device_name}, Status: {d.session_status}")

    if not device_ids:
        print("NO WEB DEVICES FOUND FOR THIS USER.")
        return

    # 2. Total messages for these devices
    total = db.query(WhatsAppInbox).filter(WhatsAppInbox.device_id.in_(device_ids)).count()
    print(f"Total messages in WhatsAppInbox for these devices: {total}")
    
    # 3. Last 10 messages across all these devices
    latest = db.query(WhatsAppInbox).filter(
        WhatsAppInbox.device_id.in_(device_ids)
    ).order_by(WhatsAppInbox.incoming_time.desc()).limit(10).all()
    
    print("Latest 10 messages details:")
    for m in latest:
        print(f"  [{m.incoming_time}] Device: {str(m.device_id)[:8]}, Phone: {m.phone_number}, Outgoing: {m.is_outgoing}, Read: {m.is_read}, Type: {m.chat_type}")

    # 4. Check for incoming messages specifically
    incoming_total = db.query(WhatsAppInbox).filter(
        WhatsAppInbox.device_id.in_(device_ids),
        WhatsAppInbox.is_outgoing == False
    ).count()
    print(f"Total INCOMING messages: {incoming_total}")

    # 5. Check time window
    seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    recent = db.query(WhatsAppInbox).filter(
        WhatsAppInbox.device_id.in_(device_ids),
        WhatsAppInbox.incoming_time >= seven_days_ago
    ).count()
    print(f"Messages in LAST 7 DAYS: {recent}")

if __name__ == "__main__":
    check_messages()
