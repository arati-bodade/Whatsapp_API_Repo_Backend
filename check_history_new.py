from db.session import SessionLocal
from models.google_sheet import GoogleSheetTriggerHistory
import uuid

s = SessionLocal()
tid = "4c373fd3-f31e-4bd9-96f0-d1f7ec036f66"
print(f"--- HISTORY FOR {tid} ---")
hist = s.query(GoogleSheetTriggerHistory).filter(GoogleSheetTriggerHistory.trigger_id == tid).all()
for h in hist:
    print(f"Row {h.row_data.get('row_number') if h.row_data else '?'}: Status={h.status}, Error={h.error_message}")
s.close()
