from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid

# Database URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost/whatsapp_platform"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check whatsapp_inbox content
    print("\n--- WhatsApp Inbox Content ---")
    result = db.execute(text("SELECT * FROM whatsapp_inbox"))
    messages = result.fetchall()
    
    if not messages:
        print("No messages found in whatsapp_inbox table.")
    else:
        print(f"Found {len(messages)} messages:")
        for msg in messages:
            print(f"- ID: {msg.id}")
            print(f"  Device: {msg.device_id}")
            print(f"  Phone: {msg.phone_number}")
            print(f"  Message: {msg.incoming_message}")
            print(f"  Replied: {msg.is_replied}")
    
    # Check Devices
    print("\n--- Devices ---")
    result = db.execute(text("SELECT device_id, device_name, session_status, busi_user_id FROM devices"))
    devices = result.fetchall()
    for dev in devices:
        print(f"- {dev.device_name} ({dev.device_id}): {dev.session_status} (User: {dev.busi_user_id})")

except Exception as e: # Catch all exceptions including table not found
    print(f"Error: {e}")
finally:
    db.close()
