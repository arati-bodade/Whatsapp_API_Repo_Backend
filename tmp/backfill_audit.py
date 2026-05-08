from db.session import SessionLocal
from models.busi_user import BusiUser
from models.audit_log import AuditLog
from models.reseller import Reseller
import uuid

def backfill():
    db = SessionLocal()
    try:
        busi_users = db.query(BusiUser).all()
        audit_count = 0
        for bu in busi_users:
            existing = db.query(AuditLog).filter(
                AuditLog.action_type == 'CREATE USER',
                AuditLog.affected_user_id == bu.busi_user_id
            ).first()
            
            if not existing:
                reseller = db.query(Reseller).filter(Reseller.reseller_id == bu.parent_reseller_id).first()
                if reseller:
                    log = AuditLog(
                        reseller_id=bu.parent_reseller_id,
                        performed_by_id=bu.parent_reseller_id,
                        performed_by_name=reseller.name or 'Reseller',
                        performed_by_role='reseller',
                        affected_user_id=bu.busi_user_id,
                        affected_user_name=bu.business_name or bu.name,
                        affected_user_email=bu.email,
                        action_type='CREATE USER',
                        module='Users',
                        description=f"Created business user {bu.business_name}",
                        changes_made=[f"initial_role: {bu.role}"],
                        created_at=bu.created_at # Backdate to the creation time
                    )
                    db.add(log)
                    audit_count += 1
        
        db.commit()
        print(f"✅ Successfully backfilled {audit_count} creation logs.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during backfill: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
