import asyncio
from db.session import SessionLocal
from models.campaign import Campaign, MessageLog

async def check():
    db = SessionLocal()
    campaign = db.query(Campaign).order_by(Campaign.created_at.desc()).first()
    print(f"Latest Campaign ID: {campaign.id}")
    print(f"Status: {campaign.status}, Sent: {campaign.sent_count}, Failed: {campaign.failed_count}")
    
    logs = db.query(MessageLog).filter(MessageLog.campaign_id == campaign.id).all()
    print(f"Total Logs: {len(logs)}")
    for log in logs:
        print(f"To: {log.recipient}, Status: {log.status}, Retry: {log.retry_count}, Delay: {log.response_time}")

if __name__ == "__main__":
    asyncio.run(check())
