import sys
sys.path.append('.')
from db.session import SessionLocal
from models.message_usage import MessageUsageCreditLog
from datetime import datetime, timedelta
import uuid

db = SessionLocal()

# Check existing logs
existing_logs = db.query(MessageUsageCreditLog).count()
print(f"Current usage logs: {existing_logs}")

if existing_logs == 0:
    # Create test usage logs
    test_logs = [
        MessageUsageCreditLog(
            usage_id="msg-" + uuid.uuid4().hex[:8],
            busi_user_id="98dd8f19-2518-4ef7-b0ea-d0c303a9e99e",
            message_id="official-single-12345",
            credits_deducted=1,
            balance_after=3999,
            timestamp=datetime.now() - timedelta(hours=2)
        ),
        MessageUsageCreditLog(
            usage_id="msg-" + uuid.uuid4().hex[:8],
            busi_user_id="98dd8f19-2518-4ef7-b0ea-d0c303a9e99e",
            message_id="unofficial-bulk-67890",
            credits_deducted=5,
            balance_after=3994,
            timestamp=datetime.now() - timedelta(hours=1)
        ),
        MessageUsageCreditLog(
            usage_id="msg-" + uuid.uuid4().hex[:8],
            busi_user_id="98dd8f19-2518-4ef7-b0ea-d0c303a9e99e",
            message_id="google-trigger-11111",
            credits_deducted=2,
            balance_after=3992,
            timestamp=datetime.now() - timedelta(minutes=30)
        ),
        MessageUsageCreditLog(
            usage_id="purchase-" + uuid.uuid4().hex[:8],
            busi_user_id="98dd8f19-2518-4ef7-b0ea-d0c303a9e99e",
            message_id="PLAN-STARTER",
            credits_deducted=-25000,  # Negative = Added
            balance_after=28992,
            timestamp=datetime.now() - timedelta(days=1)
        )
    ]
    
    for log in test_logs:
        db.add(log)
    
    db.commit()
    print(f"✅ Created {len(test_logs)} test usage logs")
else:
    print("ℹ️  Usage logs already exist")
    
    # Show recent logs
    recent_logs = db.query(MessageUsageCreditLog).order_by(MessageUsageCreditLog.timestamp.desc()).limit(5).all()
    print("\nRecent usage logs:")
    for log in recent_logs:
        sign = "+" if log.credits_deducted < 0 else ""
        print(f"  - {log.timestamp}: {log.message_id} ({sign}{log.credits_deducted} credits, balance: {log.balance_after})")

db.close()
