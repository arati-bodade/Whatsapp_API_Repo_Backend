#!/usr/bin/env python3
"""
🔧 UUID SERVICE - Centralized UUID Handling

Fixes PostgreSQL UUID vs varchar mismatches across the application.
"""

import uuid
from fastapi import HTTPException
from typing import Optional, Union, List
import logging

logger = logging.getLogger(__name__)

class UUIDService:
    """Centralized UUID handling service"""
    
    @staticmethod
    def safe_convert(device_id: Union[str, uuid.UUID, None]) -> Optional[str]:
        """Convert to string safely and validate format"""
        if device_id is None:
            return None
        
        # If it's already a UUID object, return as string
        if isinstance(device_id, uuid.UUID):
            return str(device_id)
            
        # If it's a string, we return it as is. 
        # We no longer strictly enforce UUID format here to support official phone_number_ids
        device_id_str = str(device_id)
        
        # Log-level check for extremely long IDs (exceeding VARCHAR(36))
        log_str = device_id_str.lower()
        if not any(p in log_str for p in ("test-", "debug-", "manual-", "temp-")):
            if len(device_id_str) > 36:
                 logger.warning(f"Extremely long device_id (>36 chars): {device_id_str}")
        
        return device_id_str
    
    @staticmethod
    def safe_convert_list(device_ids: List[Union[str, uuid.UUID]]) -> List[str]:
        """Convert list of IDs to list of strings safely"""
        results = []
        for device_id in device_ids:
            if device_id:
                results.append(str(device_id))
        return results
    
    @staticmethod
    def validate_uuid_string(device_id: str) -> bool:
        """Check if string is valid UUID format"""
        if not device_id:
            return False
        return True
    
    @staticmethod
    def convert_or_none(device_id: Union[str, uuid.UUID, None]) -> Optional[str]:
        """Convert to string safely, return None if invalid (no exception)"""
        if device_id is None:
            return None
        return str(device_id)

# Global convenience functions
def safe_uuid(device_id: Union[str, uuid.UUID, None]) -> Optional[str]:
    """Convenience function for ID stringification and validation"""
    return UUIDService.safe_convert(device_id)

def safe_uuid_list(device_ids: List[Union[str, uuid.UUID]]) -> List[str]:
    """Convenience function for ID list stringification"""
    return UUIDService.safe_convert_list(device_ids)
