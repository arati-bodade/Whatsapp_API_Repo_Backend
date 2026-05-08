from db.session import SessionLocal
from models.audit_log import AuditLog
import json

def check_logs():
    db = SessionLocal()
    try:
        count = db.query(AuditLog).count()
        print(f"Total Audit Logs: {count}")
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(5).all()
        for log in logs:
            print(f"ID: {log.id}, Action: {log.action_type}, Performed By: {log.performed_by_name}, Created: {log.created_at}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()
