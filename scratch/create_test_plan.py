from db.session import SessionLocal
from models.plan import Plan

db = SessionLocal()
if not db.query(Plan).filter(Plan.name == "Startup Plan").first():
    p = Plan(
        name="Startup Plan",
        price=999,
        credits_offered=1000,
        validity_days=30,
        deduction_value=1.0,
        plan_category="BUSINESS"
    )
    db.add(p)
    db.commit()
    print("Created Startup Plan")
else:
    print("Startup Plan already exists")
db.close()
