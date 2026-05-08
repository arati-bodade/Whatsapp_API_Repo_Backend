from db.session import get_db
from models.plan import Plan

db = next(get_db())
plans = db.query(Plan).all()
print(f"Total plans: {len(plans)}")
for p in plans:
    print(f"- {p.name} ({p.plan_category}) Status: {p.status}")
