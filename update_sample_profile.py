from sqlalchemy import text
from db.session import engine

def update_busi_user_profile():
    username = "mrunal123"
    print(f"Updating profile for business user: {username}...")
    with engine.connect() as connection:
        try:
            # Update business information in the businesses table
            res = connection.execute(text("""
                UPDATE businesses 
                SET 
                    business_name = :business_name,
                    organization_type = :org_type,
                    erp_system = :erp,
                    bank_name = :bank,
                    plan_name = :plan
                WHERE username = :username;
            """), {
                "business_name": "Tayade Construction",
                "org_type": "Private Limited",
                "erp": "SAP",
                "bank": "HDFC",
                "plan": "Regular Plan",
                "username": username
            })
            connection.commit()
            print(f"Successfully updated business user profile for {username}. (Rows affected: {res.rowcount})")
            
        except Exception as e:
            print(f"Error updating business user: {e}")

if __name__ == "__main__":
    update_busi_user_profile()
