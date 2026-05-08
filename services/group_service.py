from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from fastapi import HTTPException

from models.contact_group import ContactGroup, Contact, group_contacts

logger = logging.getLogger(__name__)

class GroupService:
    def __init__(self, db: Session):
        self.db = db

    def create_group(self, user_id: uuid.UUID, name: str, description: Optional[str] = None) -> ContactGroup:
        """Create a new contact group with proper commit handling."""
        try:
            if not name:
                raise HTTPException(status_code=400, detail="Group name is required")
                
            group = ContactGroup(
                user_id=user_id,
                name=name,
                description=description
            )
            
            # CRITICAL: Ensure group is committed before returning
            self.db.add(group)
            self.db.flush()      # ensures INSERT executed immediately
            self.db.commit()
            self.db.refresh(group)
            
            # Verification after commit (debug safety)
            check = self.db.query(ContactGroup).filter(ContactGroup.group_id == group.group_id).first()
            logger.info(f"[GROUP_SERVICE] Verification check group exists: {bool(check)}")
            
            logger.info(f"[GROUP_SERVICE] Created group {group.group_id} for user {user_id}")
            return group
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"[GROUP_SERVICE] Failed to create group: {e}")
            raise HTTPException(status_code=500, detail="Failed to create group")

    def add_contacts_to_group(self, group_id: uuid.UUID, user_id: uuid.UUID, contact_data: List[dict]) -> dict:
        """Add contacts to group with strong validation and transaction safety."""
        
        # STEP 1: Strong existence validation
        group = self.db.query(ContactGroup).filter(
            ContactGroup.group_id == group_id,
            ContactGroup.user_id == user_id
        ).first()
        
        if not group:
            logger.warning(f"[GROUP_SERVICE] Attempt to add contacts to missing group {group_id} by user {user_id}")
            raise HTTPException(
                status_code=404,
                detail="Group does not exist. Please refresh groups list."
            )

        if not contact_data:
            return {"success": True, "added": 0, "message": "No contacts provided"}

        # STEP 2: Validate contact format
        for item in contact_data:
            if not item.get('phone') or not item.get('name'):
                raise HTTPException(status_code=400, detail="Contact name and phone are required")

        phones_input = [item['phone'] for item in contact_data]
        
        try:
            # STEP 3: Fetch existing contacts for this user
            existing_contacts = self.db.query(Contact).filter(
                Contact.user_id == user_id,
                Contact.phone.in_(phones_input)
            ).all()
            
            existing_contact_map = {c.phone: c for c in existing_contacts}
            
            # STEP 4: Get existing group members to avoid duplicates
            existing_group_members = {
                c.phone for c in group.contacts if c.phone
            }

            added_count = 0
            
            # STEP 5: Process each contact with transaction safety
            for item in contact_data:
                # Skip if already in group
                if item['phone'] in existing_group_members:
                    continue
                    
                contact = existing_contact_map.get(item['phone'])
                
                # Create non-existent contact
                if not contact:
                    contact = Contact(
                        user_id=user_id,
                        name=item['name'],
                        phone=item['phone']
                    )
                    self.db.add(contact)
                    self.db.flush()  # Flush to assign ID
                    existing_contact_map[item['phone']] = contact
                
                # Link to group
                group.contacts.append(contact)
                existing_group_members.add(item['phone'])
                added_count += 1
                
            # STEP 6: Commit transaction
            self.db.commit()
            
            logger.info(f"[GROUP_SERVICE] Successfully added {added_count} contacts to group {group_id}")
            return {
                "success": True, 
                "added": added_count, 
                "message": f"Successfully added {added_count} contacts"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"[GROUP_SERVICE] Failed inserting contacts to group {group_id}: {e}")
            
            # Check if it's a foreign key violation
            if "foreign key constraint" in str(e).lower():
                raise HTTPException(
                    status_code=404, 
                    detail="Group not found or was deleted during operation"
                )
            raise HTTPException(status_code=500, detail="Failed to add contacts to group")

    def get_user_groups(self, user_id: uuid.UUID) -> List[ContactGroup]:
        """Get all groups for a user."""
        try:
            return self.db.query(ContactGroup).filter(
                ContactGroup.user_id == user_id
            ).all()
        except Exception as e:
            logger.error(f"[GROUP_SERVICE] Failed to get groups for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve groups")

    def delete_group(self, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a group and all its contacts."""
        try:
            group = self.db.query(ContactGroup).filter(
                ContactGroup.group_id == group_id,
                ContactGroup.user_id == user_id
            ).first()
            
            if not group:
                raise HTTPException(status_code=404, detail="Group not found")
            
            # Delete all contacts in the group first
            for contact in group.contacts:
                self.db.delete(contact)
            
            # Delete the group
            self.db.delete(group)
            self.db.commit()
            
            logger.info(f"[GROUP_SERVICE] Deleted group {group_id} for user {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"[GROUP_SERVICE] Failed to delete group {group_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete group")
