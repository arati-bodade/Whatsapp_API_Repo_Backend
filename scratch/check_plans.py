from db.session import SessionLocal
from models.plan import Plan

db = SessionLocal()
plans = db.query(Plan).all()
print(f"Total plans: {len(plans)}")
for p in plans:
    print(f"ID: {p.plan_id}, Name: {p.name}, Category: {p.plan_category}")
db.close()
