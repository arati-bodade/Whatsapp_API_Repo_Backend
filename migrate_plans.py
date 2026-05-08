from sqlalchemy import text
from db.session import SessionLocal, engine

def migrate_plans():
    print("Starting migration for plans table...")
    with engine.connect() as connection:
        try:
            # 1. Ensure table exists if not already
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS plans (
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
            print("Verified plans table existence.")
            
            # 2. Add columns if they are missing (for safety)
            cols = [
                ("name", "VARCHAR(100)"),
                ("description", "VARCHAR(255)"),
                ("price", "FLOAT"),
                ("credits_offered", "INTEGER"),
                ("validity_days", "INTEGER"),
                ("deduction_value", "FLOAT"),
                ("plan_category", "VARCHAR(50)"),
                ("status", "VARCHAR(20)"),
                ("created_at", "TIMESTAMP WITH TIME ZONE"),
                ("updated_at", "TIMESTAMP WITH TIME ZONE")
            ]
            
            for col_name, col_type in cols:
                try:
                    connection.execute(text(f"ALTER TABLE plans ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    print(f"Verified column: {col_name}")
                except Exception as col_err:
                    print(f"Skipping column {col_name} as it likely exists or can't be added.")
            
            connection.commit()
            print("Plans table migration completed.")
            
            # 3. Seed some default plans if empty
            res = connection.execute(text("SELECT count(*) FROM plans")).fetchone()
            if res[0] == 0:
                print("Seeding default plans...")
                plans_to_seed = [
                    # Business Plans
                    ("MAP 9A", 500, 1000, 30, 1.0, "BUSINESS"),
                    ("MAP 9B", 2000, 5000, 180, 1.0, "BUSINESS"),
                    ("MAP 9C", 3000, 10000, 365, 1.0, "BUSINESS"),
                    ("MAP 9D", 6000, 25000, 365, 1.0, "BUSINESS"),
                    ("MAP 9E", 11000, 50000, 365, 1.0, "BUSINESS"),
                    # Reseller Plans
                    ("STARTER", 5000, 25000, 365, 1.0, "RESELLER"),
                    ("BUSINESS", 10000, 100000, 365, 1.0, "RESELLER"),
                    ("ENTERPRISE", 50000, 600000, 365, 1.0, "RESELLER"),
                ]
                import uuid
                for name, price, credits, days, rate, cat in plans_to_seed:
                    connection.execute(text("""
                        INSERT INTO plans (plan_id, name, price, credits_offered, validity_days, deduction_value, plan_category)
                        VALUES (:id, :n, :p, :c, :v, :d, :cat)
                    """), {"id": str(uuid.uuid4()), "n": name, "p": price, "c": credits, "v": days, "d": rate, "cat": cat})
                connection.commit()
                print("Successfully seeded default plans.")
                
        except Exception as e:
            print(f"Error during plans migration: {e}")

if __name__ == "__main__":
    migrate_plans()
