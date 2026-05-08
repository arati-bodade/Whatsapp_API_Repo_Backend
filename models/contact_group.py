from sqlalchemy import Column, String, ForeignKey, Table, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import uuid

# Association table for Many-to-Many between Groups and Contacts
group_contacts = Table('group_contacts', Base.metadata,
    Column('group_id', String(36), ForeignKey('contact_groups.group_id'), primary_key=True),
    Column('contact_id', String(36), ForeignKey('contacts.contact_id'), primary_key=True)
)

class ContactGroup(Base):
    __tablename__ = "contact_groups"

    group_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Many-to-Many relationship
    contacts = relationship("Contact", secondary=group_contacts, back_populates="groups")
    user = relationship("BusiUser", back_populates="contact_groups")

class Contact(Base):
    __tablename__ = "contacts"

    contact_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("businesses.busi_user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    groups = relationship("ContactGroup", secondary=group_contacts, back_populates="contacts")
    user = relationship("BusiUser", back_populates="contacts")
