from db.session import get_db
from models.whatsapp_messages import WhatsAppMessages
from sqlalchemy import func

db = next(get_db())
count = db.query(func.count(WhatsAppMessages.id)).scalar()
print(f"Total unofficial messages: {count}")
