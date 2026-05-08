from sqlalchemy.orm import Session
from db.base import SessionLocal
from models.busi_user import BusiUser

def fix_credits():
    db: Session = SessionLocal()
    try:
        users = db.query(BusiUser).all()
        print(f"Found {len(users)} users.")
        
        fixed_count = 0
        for user in users:
            # Logic: Remaining = Allocated - Used
            # If current Remaining is different (e.g. 0), update it.
            
            allocated = user.credits_allocated or 0
            used = user.credits_used or 0
            current_remaining = user.credits_remaining or 0
            
            # Ensure none are None in DB
            user.credits_allocated = allocated
            user.credits_used = used
            
            expected_remaining = allocated - used
            
            if current_remaining != expected_remaining:
                print(f"Fixing User {user.busi_user_id}: Allocated={allocated}, Used={used}, Remaining={current_remaining} -> {expected_remaining}")
                user.credits_remaining = expected_remaining
                fixed_count += 1
                
        if fixed_count > 0:
            db.commit()
            print(f"Successfully fixed {fixed_count} users.")
        else:
            print("No users needed fixing.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_credits()
