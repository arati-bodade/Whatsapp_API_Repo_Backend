from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from core.config import settings

# Enhanced engine configuration with connection pooling
engine = settings.engine
Base = declarative_base()