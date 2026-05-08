from sqlalchemy import Column, String, DateTime, UUID as SQL_UUID
from sqlalchemy.sql import func
import uuid
from db.base import Base

class MasterAdmin(Base):
    __tablename__ = "master_admins"

    admin_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    business_name = Column(String(255), nullable=True)
    gstin = Column(String(20), nullable=True)
    bio = Column(String, nullable=True)
    location = Column(String(255), nullable=True)
    profile_image = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<MasterAdmin(admin_id={self.admin_id}, username={self.username})>"
