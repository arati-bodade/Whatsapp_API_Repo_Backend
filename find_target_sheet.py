from db.session import SessionLocal
from models.google_sheet import GoogleSheet
import json

def find_rsl_sheet(user_id):
    db = SessionLocal()
    try:
        sheets = db.query(GoogleSheet).filter(GoogleSheet.user_id == user_id).all()
        for s in sheets:
            if "rsl" in (s.sheet_name or "").lower():
                print(json.dumps({
                    "id": str(s.id),
                    "name": s.sheet_name,
                    "spreadsheet_id": s.spreadsheet_id
                }, indent=2))
                return
        
        # If not found by name, just return the first one available to avoid blockage
        if sheets:
             s = sheets[0]
             print(json.dumps({
                "id": str(s.id),
                "name": s.sheet_name,
                "spreadsheet_id": s.spreadsheet_id,
                "note": "RSL sheet not found by name, using first available."
            }, indent=2))
        else:
            print("No sheets found for user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    find_rsl_sheet("42f6886f-709e-4453-8b0b-565a49ea9c2c")
