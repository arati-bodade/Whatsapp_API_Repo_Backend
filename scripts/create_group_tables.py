from db.base import engine, Base
from models.contact_group import ContactGroup, Contact, group_contacts

def create_tables():
    print("Creating tables for Groups and Contacts...")
    try:
        # Create specific tables
        ContactGroup.__table__.create(bind=engine, checkfirst=True)
        Contact.__table__.create(bind=engine, checkfirst=True)
        group_contacts.create(bind=engine, checkfirst=True)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()
