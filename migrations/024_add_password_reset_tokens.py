from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
import secrets

Base = declarative_base()

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    token_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    user_role = Column(String, nullable=False)  # 'reseller' or 'business'
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

def upgrade():
    """Create password_reset_tokens table"""
    # Import the database configuration
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✅ Created password_reset_tokens table")

def downgrade():
    """Drop password_reset_tokens table"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    PasswordResetToken.__table__.drop(engine)
    print("✅ Dropped password_reset_tokens table")

if __name__ == "__main__":
    upgrade()
