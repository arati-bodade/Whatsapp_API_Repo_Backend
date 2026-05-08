from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from typing import List, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta
import uuid

from models.audit_log import AuditLog
from schemas.audit_log import AuditLogCreate

class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, log_data: AuditLogCreate) -> AuditLog:
        db_log = AuditLog(
            reseller_id=log_data.reseller_id,
            performed_by_id=log_data.performed_by_id,
            performed_by_name=log_data.performed_by_name,
            performed_by_role=log_data.performed_by_role,
            affected_user_id=log_data.affected_user_id,
            affected_user_name=log_data.affected_user_name,
            affected_user_email=log_data.affected_user_email,
            action_type=log_data.action_type,
            module=log_data.module,
            description=log_data.description,
            changes_made=log_data.changes_made,
            ip_address=log_data.ip_address
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    def get_logs(self, 
                 reseller_id: Optional[Any] = None, 
                 module: Optional[str] = None,
                 action: Optional[str] = None,
                 search: Optional[str] = None,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 skip: int = 0, 
                 limit: int = 50) -> Tuple[List[AuditLog], int, int]:
        
        if reseller_id:
            reseller_id = str(reseller_id)

        query = self.db.query(AuditLog)
        
        if reseller_id:
            query = query.filter(AuditLog.reseller_id == reseller_id)
            
        if module and module != "All Modules":
            query = query.filter(AuditLog.module == module)
            
        if action and action != "All Actions":
            query = query.filter(AuditLog.action_type == action)
            
        if search:
            search_filter = or_(
                AuditLog.performed_by_name.ilike(f"%{search}%"),
                AuditLog.affected_user_name.ilike(f"%{search}%"),
                AuditLog.action_type.ilike(f"%{search}%"),
                AuditLog.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
            
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
            
        total_count_query = self.db.query(func.count(AuditLog.id))
        if reseller_id:
            total_count_query = total_count_query.filter(AuditLog.reseller_id == reseller_id)
        
        total_count = total_count_query.scalar()
        filtered_count = query.count()
        
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return logs, total_count, filtered_count

    def get_last_activity_days_ago(self, reseller_id: Any) -> int:
        query = self.db.query(AuditLog.created_at)
        
        # Only filter by reseller_id if it's provided (not None or empty string)
        if reseller_id and str(reseller_id).strip():
            query = query.filter(AuditLog.reseller_id == str(reseller_id))

        last_log = query.order_by(desc(AuditLog.created_at)).first()

        if last_log and last_log[0]:
            log_time = last_log[0]
            if log_time.tzinfo is None:
                log_time = log_time.replace(tzinfo=timezone.utc)

            diff = datetime.now(timezone.utc) - log_time
            return diff.days
        return 0
