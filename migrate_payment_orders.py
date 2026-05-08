from db.base import engine
from sqlalchemy import text, inspect

insp = inspect(engine)
cols = [c['name'] for c in insp.get_columns('payment_orders')]
print('Existing columns:', cols)

with engine.connect() as conn:
    if 'allocated_to_user_id' not in cols:
        conn.execute(text('ALTER TABLE payment_orders ADD COLUMN allocated_to_user_id UUID NULL'))
        print('Added allocated_to_user_id')
    else:
        print('allocated_to_user_id already exists')
    
    if 'is_allocated' not in cols:
        conn.execute(text("ALTER TABLE payment_orders ADD COLUMN is_allocated VARCHAR(20) DEFAULT 'pending'"))
        print('Added is_allocated')
    else:
        print('is_allocated already exists')
    
    conn.commit()

print('Done.')
