from sqlalchemy import text
from db.session import engine

def update_existing_plans():
    print("Updating existing plans deduction rates to 1.0...")
    with engine.connect() as connection:
        try:
            # 1. Update all plans to 1.0 deduction rate
            res = connection.execute(text("UPDATE plans SET deduction_value = 1.0;"))
            connection.commit()
            print(f"Successfully updated plans deduction rate for {res.rowcount} plans.")
            
            # 2. Update all business users to have consumption_rate 1.0
            res_user = connection.execute(text("UPDATE businesses SET consumption_rate = 1.0 WHERE consumption_rate IS NOT NULL AND consumption_rate != 1.0;"))
            connection.commit()
            print(f"Successfully updated consumption_rate for {res_user.rowcount} business users.")
            
        except Exception as e:
            print(f"Error updating plans: {e}")

if __name__ == "__main__":
    update_existing_plans()
