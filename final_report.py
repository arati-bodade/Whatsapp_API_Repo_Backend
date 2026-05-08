from db.session import SessionLocal
from models.google_sheet import GoogleSheetTriggerHistory, GoogleSheetTrigger
from datetime import datetime, timedelta

s = SessionLocal()
now_utc = datetime.utcnow()
since_24h = now_utc - timedelta(hours=24)

print("--- TRIGGER PERFORMANCE REPORT (LAST 24H) ---")
print(f"Current UTC: {now_utc}")

# Get all history in last 24h
hist = s.query(GoogleSheetTriggerHistory).filter(GoogleSheetTriggerHistory.triggered_at >= since_24h).all()

if not hist:
    print("NO messages sent in the last 24 hours.")
else:
    print(f"Total Messages Processed: {len(hist)}")
    sent_count = len([h for h in hist if h.status == 'sent'])
    failed_count = len([h for h in hist if h.status == 'failed'])
    print(f"Successfully Sent: {sent_count}")
    print(f"Failed: {failed_count}")
    
    # Show last 5 successful deliveries
    print("\n--- LAST 5 SUCCESSFUL DELIVERIES ---")
    last_sent = s.query(GoogleSheetTriggerHistory).filter(GoogleSheetTriggerHistory.status == 'sent').order_by(GoogleSheetTriggerHistory.triggered_at.desc()).limit(5).all()
    for h in last_sent:
        print(f"Time: {h.triggered_at} (UTC) | Row {h.row_data.get('row_number') if h.row_data else '?'} | Trigger: {h.trigger_id}")

s.close()
