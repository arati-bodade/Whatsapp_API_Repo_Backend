import asyncio
from core.redis_client import redis_client
from db.session import SessionLocal
from models.google_sheet import GoogleSheet

async def check_connectivity():

    print("\nChecking Database...")
    try:
        db = SessionLocal()
        sheet = db.query(GoogleSheet).first()
        print(f"✅ Database Connected. Found sheet: {sheet.id if sheet else 'None'}")
        db.close()
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_connectivity())
