from sqlalchemy import text
from db.session import SessionLocal, engine
import uuid

def recreate_plans_table():
    print("Starting recreation of plans table to match model...")
    with engine.connect() as connection:
        try:
            # 1. Rename existing table if it exists
            try:
                connection.execute(text("ALTER TABLE plans RENAME TO plans_old_backup;"))
                print("Renamed existing 'plans' table to 'plans_old_backup'.")
            except Exception as e:
                print("No existing 'plans' table to rename or rename failed (likely handles manually).")
            
            # 2. Create fresh table
            connection.execute(text("""
                CREATE TABLE plans (
                    plan_id UUID PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description VARCHAR(255),
                    price FLOAT DEFAULT 0.0,
                    credits_offered INTEGER DEFAULT 0,
                    validity_days INTEGER DEFAULT 30,
                    deduction_value FLOAT DEFAULT 0.25,
                    plan_category VARCHAR(50) DEFAULT 'BUSINESS',
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """))
            print("Created fresh 'plans' table.")
            
            # 3. Seed default plans
            plans_to_seed = [
                # Business Plans
                ("MAP 9A", 500, 1000, 30, 0.5, "BUSINESS"),
                ("MAP 9B", 2000, 5000, 180, 0.4, "BUSINESS"),
                ("MAP 9C", 3000, 10000, 365, 0.3, "BUSINESS"),
                ("MAP 9D", 6000, 25000, 365, 0.24, "BUSINESS"),
                ("MAP 9E", 11000, 50000, 365, 0.22, "BUSINESS"),
                # Reseller Plans
                ("STARTER", 5000, 25000, 365, 0.20, "RESELLER"),
                ("BUSINESS", 10000, 100000, 365, 0.10, "RESELLER"),
                ("ENTERPRISE", 50000, 600000, 365, 0.08, "RESELLER"),
                ("DEMO", 0, 30, 3, 0, "BUSINESS"),
            ]
            
            for name, price, credits, days, rate, cat in plans_to_seed:
                connection.execute(text("""
                    INSERT INTO plans (plan_id, name, price, credits_offered, validity_days, deduction_value, plan_category)
                    VALUES (:id, :n, :p, :c, :v, :d, :cat)
                """), {
                    "id": str(uuid.uuid4()), 
                    "n": name, 
                    "p": price, 
                    "c": credits, 
                    "v": days, 
                    "d": rate, 
                    "cat": cat
                })
            
            connection.commit()
            print("Successfully seeded default plans into the fresh table.")
            
        except Exception as e:
            print(f"Error during plans recreation: {e}")

if __name__ == "__main__":
    recreate_plans_table()
