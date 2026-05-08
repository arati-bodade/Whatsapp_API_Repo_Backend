"""
Fix allocation status for existing payment orders.
This script updates orders that have status='success' but is_allocated='pending'
to is_allocated='allocated' since credits were already added to the wallet.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.payment_order import PaymentOrder

def fix_allocation_status():
    """Update allocation status for successful orders."""
    db: Session = SessionLocal()
    try:
        # Find all successful orders with pending allocation
        orders_to_fix = db.query(PaymentOrder).filter(
            PaymentOrder.status == "success",
            PaymentOrder.is_allocated == "pending"
        ).all()
        
        print(f"Found {len(orders_to_fix)} orders to fix")
        
        for order in orders_to_fix:
            # Update to allocated
            order.is_allocated = "allocated"
            print(f"Updated order {order.txnid} - {order.plan_name} - {order.credits} credits")
        
        db.commit()
        print(f"Successfully updated {len(orders_to_fix)} orders")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_allocation_status()
