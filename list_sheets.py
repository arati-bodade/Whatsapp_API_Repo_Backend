from db.session import SessionLocal
from models.google_sheet import GoogleSheet
import json

def list_sheets():
    db = SessionLocal()
    try:
        sheets = db.query(GoogleSheet).all()
        result = []
        for s in sheets:
            result.append({
                "id": str(s.id),
                "spreadsheet_id": s.spreadsheet_id,
                "name": s.sheet_name,
                "user_id": str(s.user_id)
            })
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_sheets()
