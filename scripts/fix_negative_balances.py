from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.message_usage import MessageUsageCreditLog

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./whatsapp_platform.db" # Check if this is correct

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_negative_balances():
    db = SessionLocal()
    try:
        # Find all logs with negative balance_after
        negative_logs = db.query(MessageUsageCreditLog).filter(MessageUsageCreditLog.balance_after < 0).all()
        print(f"Found {len(negative_logs)} logs with negative balance.")
        
        for log in negative_logs:
            print(f"Fixing log {log.usage_id}: balance_after {log.balance_after} -> 0")
            log.balance_after = 0
            
        db.commit()
        print("Fixed all negative balances.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_negative_balances()
