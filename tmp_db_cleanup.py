from db.session import SessionLocal
from models.plan import Plan

def cleanup_plans():
    db = SessionLocal()
    try:
        plans = db.query(Plan).all()
        for p in plans:
            p.name = p.name.strip()
            p.plan_category = p.plan_category.strip().upper()
            print(f"Cleaned up: '{p.name}' -> '{p.plan_category}'")
        db.commit()
        print(f"Total cleaned: {len(plans)}")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_plans()
