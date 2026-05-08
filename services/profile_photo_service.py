"""
Profile Photo Service
Handles profile photo operations for users, resellers, and admins
"""

import os
import uuid
import shutil
from typing import Optional
from PIL import Image
import io
from datetime import datetime

from sqlalchemy.orm import Session
from models.busi_user import BusiUser
from models.reseller import Reseller
from models.admin import MasterAdmin

class ProfilePhotoService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = "uploads/profile_images"
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        self.max_dimensions = (1024, 1024)
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(os.path.join(self.upload_dir, 'users'), exist_ok=True)
        os.makedirs(os.path.join(self.upload_dir, 'resellers'), exist_ok=True)
        os.makedirs(os.path.join(self.upload_dir, 'admins'), exist_ok=True)
    
    def _generate_filename(self, user_id: str, extension: str) -> str:
        """Generate unique filename for profile photo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{user_id}_{timestamp}_{unique_id}{extension}"
    
    def _validate_file(self, file) -> tuple[bool, Optional[str]]:
        """Validate uploaded file"""
        # Check file extension
        if hasattr(file, 'filename'):
            _, ext = os.path.splitext(file.filename.lower())
            if ext not in self.allowed_extensions:
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
        
        return True, None
    
    def _resize_image(self, file_data: bytes, max_size: tuple = (1024, 1024)) -> bytes:
        """Resize image if it's too large"""
        try:
            image = Image.open(io.BytesIO(file_data))
            
            # Check if image needs resizing
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary (for JPEG)
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                    image = background
                
                # Save to bytes
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85, optimize=True)
                return buffer.getvalue()
            
            return file_data
        except Exception as e:
            # If resizing fails, return original data
            return file_data
    
    def _get_user_model(self, user_type: str):
        """Get the appropriate model based on user type"""
        if user_type == 'user':
            return BusiUser
        elif user_type == 'reseller':
            return Reseller
        elif user_type == 'admin':
            return MasterAdmin
        else:
            raise ValueError(f"Invalid user type: {user_type}")
    
    def _get_user_id_field(self, user_type: str):
        """Get the user ID field name for the user type"""
        if user_type == 'user':
            return 'busi_user_id'
        elif user_type == 'reseller':
            return 'reseller_id'
        elif user_type == 'admin':
            return 'admin_id'
        else:
            raise ValueError(f"Invalid user type: {user_type}")
    
    def save_profile_photo(self, file, user_type: str, user_id: str) -> str:
        """Save profile photo and update database"""
        import asyncio
        
        # Validate file
        is_valid, error = self._validate_file(file)
        if not is_valid:
            raise ValueError(error)
        
        # Get file extension
        _, ext = os.path.splitext(file.filename.lower())
        
        # Generate filename
        filename = self._generate_filename(user_id, ext)
        
        # Create user-specific directory
        user_dir_name = user_type + 's'
        user_dir = os.path.join(self.upload_dir, user_dir_name)
        file_path = os.path.join(user_dir, filename)
        
        # Read file data (handle FastAPI UploadFile)
        if hasattr(file, 'read'):
            # For FastAPI UploadFile, we need to read it properly
            file_data = file.file.read()
        else:
            # Fallback for other file types
            file_data = file.read()
        
        # Resize image
        file_data = self._resize_image(file_data)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Update database
        model = self._get_user_model(user_type)
        id_field = self._get_user_id_field(user_type)
        
        user = self.db.query(model).filter(getattr(model, id_field) == user_id).first()
        if user:
            # Delete old photo if exists
            if user.profile_image:
                # Normalize path for deletion
                normalized_old_path = user.profile_image.replace('/', os.sep).replace('\\', os.sep)
                old_file_path = os.path.join(self.upload_dir, normalized_old_path)
                if os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except Exception as e:
                        print(f"Error removing old profile photo: {e}")
            
            # Update profile_image field (use forward slashes for cross-platform compatibility)
            # Store the full relative path starting with /uploads/profile_images/
            relative_path = f"/uploads/profile_images/{user_dir_name}/{filename}"
            user.profile_image = relative_path
            self.db.commit()
            return relative_path
        
        return f"/uploads/profile_images/{user_dir_name}/{filename}"
    
    def update_profile_photo(self, file, user_type: str, user_id: str) -> str:
        """Update existing profile photo"""
        return self.save_profile_photo(file, user_type, user_id)
    
    def delete_profile_photo(self, user_type: str, user_id: str) -> bool:
        """Delete profile photo and update database"""
        try:
            # Get user from database
            model = self._get_user_model(user_type)
            id_field = self._get_user_id_field(user_type)
            
            user = self.db.query(model).filter(getattr(model, id_field) == user_id).first()
            if not user or not user.profile_image:
                return False
            
            # Delete file
            # The path in DB now includes /uploads/profile_images/
            # We need to strip it to get the path relative to the root for deletion
            db_path = user.profile_image
            if db_path.startswith('/uploads/profile_images/'):
                relative_disk_path = db_path.replace('/uploads/profile_images/', '')
            elif db_path.startswith('uploads/profile_images/'):
                relative_disk_path = db_path.replace('uploads/profile_images/', '')
            else:
                relative_disk_path = db_path
                
            normalized_path = relative_disk_path.replace('/', os.sep).replace('\\', os.sep)
            file_path = os.path.join(self.upload_dir, normalized_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Update database
            user.profile_image = None
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_profile_photo_url(self, user_type: str, user_id: str) -> Optional[str]:
        """Get profile photo URL for user"""
        try:
            # Get user from database
            model = self._get_user_model(user_type)
            id_field = self._get_user_id_field(user_type)
            
            user = self.db.query(model).filter(getattr(model, id_field) == user_id).first()
            if not user or not user.profile_image:
                return None
            
            # Return path directly as it now includes the prefix
            path = user.profile_image
            if not path.startswith('/'):
                path = f"/{path}"
                
            return path
        except Exception as e:
            print(f"Error getting profile photo URL: {e}")
            return None
    
    def cleanup_unused_photos(self) -> int:
        """Clean up unused profile photos"""
        cleaned_count = 0
        
        try:
            # Get all photos in database
            all_db_photos = set()
            
            # Check users
            users = self.db.query(BusiUser).filter(BusiUser.profile_image.isnot(None)).all()
            for user in users:
                if user.profile_image:
                    all_db_photos.add(user.profile_image.replace('\\', '/'))
            
            # Check resellers
            resellers = self.db.query(Reseller).filter(Reseller.profile_image.isnot(None)).all()
            for reseller in resellers:
                if reseller.profile_image:
                    all_db_photos.add(reseller.profile_image.replace('\\', '/'))
            
            # Check admins
            admins = self.db.query(MasterAdmin).filter(MasterAdmin.profile_image.isnot(None)).all()
            for admin in admins:
                if admin.profile_image:
                    all_db_photos.add(admin.profile_image.replace('\\', '/'))
            
            # Check files on disk
            for user_type in ['users', 'resellers', 'admins']:
                user_dir = os.path.join(self.upload_dir, user_type)
                if os.path.exists(user_dir):
                    for filename in os.listdir(user_dir):
                        file_path = f"{user_type}/{filename}"
                        if file_path not in all_db_photos:
                            full_path = os.path.join(self.upload_dir, filename) # Wait, filename is not full path
                            # Correct path construction
                            full_path = os.path.join(self.upload_dir, user_type, filename)
                            if os.path.isfile(full_path):
                                os.remove(full_path)
                                cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            raise e
    
    def get_statistics(self) -> dict:
        """Get profile photo statistics"""
        try:
            stats = {
                'total_users_with_photos': 0,
                'total_resellers_with_photos': 0,
                'total_admins_with_photos': 0,
                'total_photos': 0,
                'storage_used': 0
            }
            
            # Count users with photos
            stats['total_users_with_photos'] = self.db.query(BusiUser).filter(
                BusiUser.profile_image.isnot(None)
            ).count()
            
            # Count resellers with photos
            stats['total_resellers_with_photos'] = self.db.query(Reseller).filter(
                Reseller.profile_image.isnot(None)
            ).count()
            
            # Count admins with photos
            stats['total_admins_with_photos'] = self.db.query(MasterAdmin).filter(
                MasterAdmin.profile_image.isnot(None)
            ).count()
            
            stats['total_photos'] = (
                stats['total_users_with_photos'] + 
                stats['total_resellers_with_photos'] + 
                stats['total_admins_with_photos']
            )
            
            # Calculate storage used
            for user_type in ['users', 'resellers', 'admins']:
                user_dir = os.path.join(self.upload_dir, user_type)
                if os.path.exists(user_dir):
                    for filename in os.listdir(user_dir):
                        file_path = os.path.join(user_dir, filename)
                        if os.path.isfile(file_path):
                            stats['storage_used'] += os.path.getsize(file_path)
            
            return stats
        except Exception as e:
            raise e
