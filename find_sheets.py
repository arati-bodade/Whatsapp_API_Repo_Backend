from db.session import SessionLocal
from models.google_sheet import GoogleSheet
import json

def get_sheets(user_id):
    db = SessionLocal()
    try:
        sheets = db.query(GoogleSheet).filter(GoogleSheet.user_id == user_id).all()
        sheet_list = []
        for s in sheets:
            sheet_list.append({
                "id": str(s.id),
                "name": s.sheet_name,
                "spreadsheet_id": s.spreadsheet_id
            })
        print(json.dumps(sheet_list, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    get_sheets("42f6886f-709e-4453-8b0b-565a49ea9c2c")
