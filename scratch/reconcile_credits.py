from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models.reseller import Reseller
from models.message_usage import MessageUsageCreditLog
import logging

DATABASE_URL = "postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# 1. Find Arati's reseller account
reseller = session.query(Reseller).filter(Reseller.name.ilike('%Arati%')).first()

if reseller:
    print(f"Found Reseller: {reseller.name} ({reseller.reseller_id})")
    print(f"Current Available: {reseller.available_credits}, Used: {reseller.used_credits}, Total: {reseller.total_credits}")
    
    # 2. Find leaked message deductions (source is NOT distribution)
    leaked_deductions = session.query(func.sum(MessageUsageCreditLog.credits_deducted)).filter(
        MessageUsageCreditLog.busi_user_id == reseller.reseller_id,
        MessageUsageCreditLog.source != 'distribution',
        MessageUsageCreditLog.credits_deducted > 0
    ).scalar() or 0
    
    print(f"Leaked Deductions Found: {leaked_deductions}")
    
    if leaked_deductions > 0:
        print(f"Refunding {leaked_deductions} credits...")
        reseller.available_credits += leaked_deductions
        reseller.used_credits -= leaked_deductions
        
        # Verify consistency
        if reseller.total_credits != (reseller.available_credits + reseller.used_credits):
            print("Warning: Balance inconsistency after refund. Force adjusting used_credits.")
            reseller.used_credits = reseller.total_credits - reseller.available_credits
            
        session.commit()
        print(f"New Balances - Available: {reseller.available_credits}, Used: {reseller.used_credits}")
    else:
        print("No leaked deductions found to refund.")
else:
    print("Reseller Arati not found.")

session.close()
