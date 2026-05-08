from db.session import engine
from models.whatsapp_inbox import WhatsAppInbox
from sqlalchemy.orm import sessionmaker
from datetime import timezone

Session = sessionmaker(bind=engine)
session = Session()

try:
    # Get the latest message
    msg = session.query(WhatsAppInbox).order_by(WhatsAppInbox.incoming_time.desc()).first()
    if msg:
        print(f"Message ID: {msg.id}")
        print(f"Original Incoming Time: {msg.incoming_time} (tzinfo: {msg.incoming_time.tzinfo})")
        
        # Apply the fix logic
        if msg.incoming_time.tzinfo is None:
            fixed_time = msg.incoming_time.replace(tzinfo=timezone.utc)
        else:
            fixed_time = msg.incoming_time
            
        print(f"Fixed Incoming Time: {fixed_time} (tzinfo: {fixed_time.tzinfo})")
        print(f"ISO Format: {fixed_time.isoformat()}")
    else:
        print("No messages found in database.")
finally:
    session.close()
