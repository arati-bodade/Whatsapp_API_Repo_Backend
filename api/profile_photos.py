"""
Profile Photos API
Handles CRUD operations for user profile photos
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from datetime import datetime

from db.session import get_db
from api.auth import get_current_user
from services.profile_photo_service import ProfilePhotoService

router = APIRouter()

@router.get("/me")
async def get_my_profile_photo(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile photo information"""
    try:
        profile_service = ProfilePhotoService(db)
        
        # Determine user type and ID based on user role
        user_role = getattr(current_user, 'role_in_token', 'business_owner').lower()
        user_id = getattr(current_user, 'busi_user_id', None) or getattr(current_user, 'reseller_id', None) or getattr(current_user, 'admin_id', None)
        
        if 'business' in user_role or 'busi' in user_role:
            user_type = 'user'
        elif 'reseller' in user_role:
            user_type = 'reseller'
        elif 'admin' in user_role:
            user_type = 'admin'
        else:
            user_type = 'user'  # default
        
        # Get profile photo URL
        photo_url = profile_service.get_profile_photo_url(user_type, user_id)
        
        return {
            "photo_url": photo_url,
            "user_type": user_type,
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile photo: {str(e)}")

@router.post("/upload")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new profile photo"""
    try:
        profile_service = ProfilePhotoService(db)
        
        # Determine user type and ID
        user_role = getattr(current_user, 'role_in_token', 'business_owner').lower()
        user_id = getattr(current_user, 'busi_user_id', None) or getattr(current_user, 'reseller_id', None) or getattr(current_user, 'admin_id', None)
        
        if 'business' in user_role or 'busi' in user_role:
            user_type = 'user'
        elif 'reseller' in user_role:
            user_type = 'reseller'
        elif 'admin' in user_role:
            user_type = 'admin'
        else:
            user_type = 'user'  # default
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save profile photo
        file_path = profile_service.save_profile_photo(file, user_type, user_id)
        
        # Get photo URL
        photo_url = profile_service.get_profile_photo_url(user_type, user_id)
        
        return {
            "message": "Profile photo uploaded successfully",
            "url": photo_url,
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload profile photo: {str(e)}")

@router.put("/update")
async def update_profile_photo(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update existing profile photo"""
    try:
        profile_service = ProfilePhotoService(db)
        
        # Determine user type and ID
        user_role = getattr(current_user, 'role_in_token', 'business_owner').lower()
        user_id = getattr(current_user, 'busi_user_id', None) or getattr(current_user, 'reseller_id', None) or getattr(current_user, 'admin_id', None)
        
        if 'business' in user_role or 'busi' in user_role:
            user_type = 'user'
        elif 'reseller' in user_role:
            user_type = 'reseller'
        elif 'admin' in user_role:
            user_type = 'admin'
        else:
            user_type = 'user'  # default
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Update profile photo
        file_path = profile_service.update_profile_photo(file, user_type, user_id)
        
        # Get photo URL
        photo_url = profile_service.get_profile_photo_url(user_type, user_id)
        
        return {
            "message": "Profile photo updated successfully",
            "url": photo_url,
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile photo: {str(e)}")

@router.delete("/delete")
async def delete_profile_photo(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete profile photo"""
    try:
        profile_service = ProfilePhotoService(db)
        
        # Determine user type and ID
        user_role = getattr(current_user, 'role_in_token', 'business_owner').lower()
        user_id = getattr(current_user, 'busi_user_id', None) or getattr(current_user, 'reseller_id', None) or getattr(current_user, 'admin_id', None)
        
        if 'business' in user_role or 'busi' in user_role:
            user_type = 'user'
        elif 'reseller' in user_role:
            user_type = 'reseller'
        elif 'admin' in user_role:
            user_type = 'admin'
        else:
            user_type = 'user'  # default
        
        # Delete profile photo
        deleted = profile_service.delete_profile_photo(user_type, user_id)
        
        return {
            "message": "Profile photo deleted successfully",
            "deleted": deleted
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete profile photo: {str(e)}")

@router.get("/view/{user_type}/{user_id}")
async def view_profile_photo(
    user_type: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """View a user's profile photo (public endpoint)"""
    try:
        profile_service = ProfilePhotoService(db)
        
        # Validate user type
        if user_type not in ['user', 'reseller', 'admin']:
            raise HTTPException(status_code=400, detail="Invalid user type")
        
        # Get photo URL
        photo_url = profile_service.get_profile_photo_url(user_type, user_id)
        
        if not photo_url:
            raise HTTPException(status_code=404, detail="Profile photo not found")
        
        return {
            "photo_url": photo_url,
            "user_type": user_type,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile photo: {str(e)}")

@router.get("/user/{user_id}")
async def get_user_profile_photo(
    user_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user's profile photo (admin only)"""
    try:
        # Check if current user is admin
        user_role = getattr(current_user, 'role_in_token', 'business_owner').lower()
        if 'admin' not in user_role:
            raise HTTPException(status_code=403, detail="Access denied")
        
        profile_service = ProfilePhotoService(db)
        
        # Try different user types to find the user
        for user_type in ['user', 'reseller', 'admin']:
            photo_url = profile_service.get_profile_photo_url(user_type, user_id)
            if photo_url:
                return {
                    "photo_url": photo_url,
                    "user_type": user_type,
                    "user_id": user_id
                }
        
        raise HTTPException(status_code=404, detail="Profile photo not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile photo: {str(e)}")

@router.post("/cleanup")
async def cleanup_unused_photos(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up unused profile photos (admin only)"""
    try:
        # Check if current user is admin
        user_role = getattr(current_user, 'role_in_token', 'business_owner').lower()
        if 'admin' not in user_role:
            raise HTTPException(status_code=403, detail="Access denied")
        
        profile_service = ProfilePhotoService(db)
        
        # Clean up unused photos
        cleaned_count = profile_service.cleanup_unused_photos()
        
        return {
            "message": f"Cleaned up {cleaned_count} unused photos",
            "cleaned_count": cleaned_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup photos: {str(e)}")

@router.get("/stats")
async def get_profile_photo_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profile photo statistics (admin only)"""
    try:
        # Check if current user is admin
        user_role = getattr(current_user, 'role_in_token', 'business_owner').lower()
        if 'admin' not in user_role:
            raise HTTPException(status_code=403, detail="Access denied")
        
        profile_service = ProfilePhotoService(db)
        
        # Get statistics
        stats = profile_service.get_statistics()
        
        return {
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
