from sqlalchemy.orm import Session
from db.base import SessionLocal
from models.contact_group import ContactGroup, Contact
from models.busi_user import BusiUser
import uuid

def seed_groups():
    db: Session = SessionLocal()
    try:
        # Get first user
        user = db.query(BusiUser).first()
        if not user:
            print("No Business User found to seed.")
            return

        print(f"Seeding groups for user: {user.username} ({user.busi_user_id})")

        groups_data = ["VIP Customers", "New Leads", "Beta Testers", "Support Team"]
        created_groups = []

        for name in groups_data:
            group = db.query(ContactGroup).filter(ContactGroup.user_id == user.busi_user_id, ContactGroup.name == name).first()
            if not group:
                group = ContactGroup(
                    group_id=uuid.uuid4(),
                    user_id=user.busi_user_id,
                    name=name,
                    description=f"Group for {name}"
                )
                db.add(group)
                print(f"Created group: {name}")
            else:
                print(f"Group exists: {name}")
            created_groups.append(group)
        
        db.commit()

        # Add dummy contacts
        print("Seeding contacts...")
        for i in range(1, 11):
            phone = f"91987654320{i}" # Dummy numbers
            contact = db.query(Contact).filter(Contact.user_id == user.busi_user_id, Contact.phone == phone).first()
            if not contact:
                contact = Contact(
                    contact_id=uuid.uuid4(),
                    user_id=user.busi_user_id,
                    name=f"Demo Contact {i}",
                    phone=phone
                )
                db.add(contact)
                print(f"Created/Found contact: {phone}")
            
            # Link to groups
            # Link to VIP Customers (index 0) if even
            if i % 2 == 0:
                if contact not in created_groups[0].contacts:
                    created_groups[0].contacts.append(contact)
            
            # Link to New Leads (index 1) if odd
            if i % 2 != 0:
                 if contact not in created_groups[1].contacts:
                    created_groups[1].contacts.append(contact)
        
        db.commit()
        print("Seeding complete successfully.")

    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_groups()
