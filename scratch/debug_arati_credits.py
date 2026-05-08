import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models.reseller import Reseller
from models.credit_distribution import CreditDistribution
from models.busi_user import BusiUser

DATABASE_URL = "postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

reseller = session.query(Reseller).filter(Reseller.name.ilike('%Arati%')).first()

if reseller:
    print(f"Reseller: {reseller.name} ({reseller.reseller_id})")
    
    # Check distributions
    distributions = session.query(CreditDistribution).filter(CreditDistribution.from_reseller_id == reseller.reseller_id).all()
    print(f"Total Distributions found: {len(distributions)}")
    total_d = 0
    for d in distributions:
        print(f"  To: {d.to_business_user_id}, Credits: {d.credits_shared}, At: {d.shared_at}")
        total_d += d.credits_shared
    print(f"Sum of distributions: {total_d}")
    
    # Check sub-users and their allocated credits
    sub_users = session.query(BusiUser).filter(BusiUser.parent_reseller_id == reseller.reseller_id).all()
    print(f"Sub-users found: {len(sub_users)}")
    for u in sub_users:
        print(f"  User: {u.business_name} ({u.busi_user_id}), Allocated: {u.credits_allocated}, Remaining: {u.credits_remaining}")

else:
    print("Reseller not found.")

session.close()
