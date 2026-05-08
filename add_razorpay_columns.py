#!/usr/bin/env python3
"""Add Razorpay columns to payment_orders table"""

from db.session import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print('=== Adding Razorpay Columns to Payment Orders ===')
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'payment_orders' 
            AND column_name IN ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        """))
        
        existing_columns = [row[0] for row in result.fetchall()]
        print(f'Existing columns: {existing_columns}')
        
        # Add missing columns
        if 'razorpay_order_id' not in existing_columns:
            db.execute(text('ALTER TABLE payment_orders ADD COLUMN razorpay_order_id VARCHAR(100)'))
            print('✅ Added razorpay_order_id column')
        
        if 'razorpay_payment_id' not in existing_columns:
            db.execute(text('ALTER TABLE payment_orders ADD COLUMN razorpay_payment_id VARCHAR(100)'))
            print('✅ Added razorpay_payment_id column')
        
        if 'razorpay_signature' not in existing_columns:
            db.execute(text('ALTER TABLE payment_orders ADD COLUMN razorpay_signature VARCHAR(255)'))
            print('✅ Added razorpay_signature column')
        
        db.commit()
        print('\n✅ All Razorpay columns added successfully!')
        
    except Exception as e:
        print(f'❌ Error adding columns: {e}')
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
