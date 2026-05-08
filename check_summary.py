from db.session import get_db
from services.message_usage_service import MessageUsageService

db = next(get_db())
service = MessageUsageService(db)
user_id = "a4ea62f8-b476-4c80-810b-f8f681029944"
summary = service.get_credit_summary(user_id)
print(f"Summary for {user_id}: {summary}")
