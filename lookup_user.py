from db.session import SessionLocal
from models.busi_user import BusiUser
from models.google_sheet import GoogleSheet
import json

def get_user_and_sheets(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email.lower().strip()).first()
        if not user:
            print(f"User with email {email} not found.")
            return

        print(f"User Found: {user.busi_user_id} ({user.name})")
        
        sheets = db.query(GoogleSheet).filter(GoogleSheet.user_id == user.busi_user_id).all()
        sheet_list = []
        for s in sheets:
            sheet_list.append({
                "id": str(s.id),
                "name": s.sheet_name,
                "spreadsheet_id": s.spreadsheet_id
            })
        print("Sheets Found:")
        print(json.dumps(sheet_list, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    get_user_and_sheets("amit.verma@testmail.com")
