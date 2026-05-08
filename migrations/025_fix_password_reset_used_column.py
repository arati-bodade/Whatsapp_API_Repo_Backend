from sqlalchemy import create_engine, text
import sys
import os

def upgrade():
    """Alter password_reset_tokens.used column from VARCHAR to BOOLEAN"""
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Convert existing string values to boolean
        conn.execute(text("""
            UPDATE password_reset_tokens 
            SET used = 'false' 
            WHERE used IS NULL OR used = ''
        """))
        
        # Alter column type to BOOLEAN
        conn.execute(text("""
            ALTER TABLE password_reset_tokens 
            ALTER COLUMN used TYPE BOOLEAN 
            USING CASE 
                WHEN used = 'true' THEN true 
                WHEN used = 'false' THEN false 
                ELSE false 
            END
        """))
        
        conn.commit()
    
    print("✅ Fixed password_reset_tokens.used column to BOOLEAN type")

def downgrade():
    """Revert password_reset_tokens.used column back to VARCHAR"""
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Alter column type back to VARCHAR
        conn.execute(text("""
            ALTER TABLE password_reset_tokens 
            ALTER COLUMN used TYPE VARCHAR 
            USING CASE 
                WHEN used = true THEN 'true' 
                WHEN used = false THEN 'false' 
                ELSE 'false' 
            END
        """))
        
        conn.commit()
    
    print("✅ Reverted password_reset_tokens.used column to VARCHAR type")

if __name__ == "__main__":
    upgrade()
