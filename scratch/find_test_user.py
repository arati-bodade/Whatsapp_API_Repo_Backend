from sqlalchemy import create_engine
import os

# Using the URL from core/config.py
DATABASE_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Try to find an admin or reseller
    result = conn.execute("SELECT email, username, role FROM resellers LIMIT 1")
    reseller = result.fetchone()
    if reseller:
        print(f"Reseller: {reseller}")
    
    result = conn.execute("SELECT email, username, name FROM businesses LIMIT 1")
    business = result.fetchone()
    if business:
        print(f"Business: {business}")
    
    result = conn.execute("SELECT email, username FROM master_admins LIMIT 1")
    admin = result.fetchone()
    if admin:
        print(f"Admin: {admin}")
