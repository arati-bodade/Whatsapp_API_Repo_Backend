from db.session import SessionLocal
from models.google_sheet import GoogleSheetTrigger
import models

def print_trigger_details():
    db = SessionLocal()
    try:
        tid = '1307b3d8-1361-495a-aff2-dbaa90288de1'
        t = db.query(GoogleSheetTrigger).filter(GoogleSheetTrigger.trigger_id == tid).first()
        if t:
            print(f"Trigger {tid}:")
            for column in t.__table__.columns:
                print(f"  {column.name}: {getattr(t, column.name)}")
        else:
            print("Trigger not found")
    finally:
        db.close()

if __name__ == "__main__":
    print_trigger_details()
