import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

from models.reseller import Reseller

resellers = session.query(Reseller).filter(Reseller.name.ilike('%Arati%')).all()
for r in resellers:
    print(f"ID: {r.reseller_id}, Name: {r.name}, Available: {r.available_credits}, Used: {r.used_credits}, Total: {r.total_credits}")

session.close()
