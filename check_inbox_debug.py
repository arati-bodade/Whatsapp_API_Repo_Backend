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
    device_id = "dbfc3dc8-fe47-4133-a466-3cdd118bf12b"
    
    # Check if device exists
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        print(f"Device found: {device.device_name}, Type: {device.device_type}, User ID: {device.busi_user_id}")
    else:
        print(f"Device not found for ID {device_id}!")
        return

    # Count total messages for this device
    total_count = db.query(WhatsAppInbox).filter(WhatsAppInbox.device_id == device_id).count()
    print(f"Total messages for this device: {total_count}")
    
    # Count incoming messages
    incoming_count = db.query(WhatsAppInbox).filter(
        WhatsAppInbox.device_id == device_id,
        WhatsAppInbox.is_outgoing == False
    ).count()
    print(f"Incoming messages count: {incoming_count}")
    
    # Count unread messages
    unread_count = db.query(WhatsAppInbox).filter(
        WhatsAppInbox.device_id == device_id,
        WhatsAppInbox.is_read == False
    ).count()
    print(f"Unread messages count: {unread_count}")
    
    # Recent messages (last 7 days)
    seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    recent_count = db.query(WhatsAppInbox).filter(
        WhatsAppInbox.device_id == device_id,
        WhatsAppInbox.incoming_time >= seven_days_ago
    ).count()
    print(f"Messages in last 7 days: {recent_count}")
    
    # Latest 5 messages
    latest_messages = db.query(WhatsAppInbox).filter(WhatsAppInbox.device_id == device_id).order_by(WhatsAppInbox.incoming_time.desc()).limit(5).all()
    for m in latest_messages:
        print(f"  [{m.incoming_time}] Outgoing: {m.is_outgoing}, Read: {m.is_read}, Phone: {m.phone_number}")

    # Check for all user's devices
    any_device_ids = db.query(Device.device_id).filter(Device.busi_user_id == user_id).all()
    any_device_ids = [str(d[0]) for d in any_device_ids]
    print(f"User's devices: {any_device_ids}")
    
    any_messages = db.query(WhatsAppInbox).filter(WhatsAppInbox.device_id.in_(any_device_ids)).count()
    print(f"Total messages for ANY of this user's devices: {any_messages}")

if __name__ == "__main__":
    check_messages()
