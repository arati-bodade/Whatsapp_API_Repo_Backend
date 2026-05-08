#!/usr/bin/env python3
"""
🔥 META WHATSAPP TOKEN MANAGEMENT SERVICE

Handles:
- Token validation
- Token expiry detection
- Token refresh alerts
- Permanent token recommendations
"""

import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from models.official_whatsapp_config import OfficialWhatsAppConfig

logger = logging.getLogger(__name__)

class TokenService:
    """Meta WhatsApp Token Management Service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.meta_api_base_url = "https://graph.facebook.com/v18.0"
    
    def validate_token(self, config: OfficialWhatsAppConfig) -> Dict[str, Any]:
        """
        Validate Meta WhatsApp access token
        
        Returns:
            Dict with validation status and details
        """
        try:
            # Test token with Meta API
            url = f"{self.meta_api_base_url}/{config.phone_number_id}"
            headers = {"Authorization": f"Bearer {config.access_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True,
                    "status": "active",
                    "phone_number": data.get("display_phone_number"),
                    "verified_name": data.get("verified_name"),
                    "name_status": data.get("name_status"),
                    "quality_rating": data.get("quality_rating"),
                    "message": "Token is valid and active"
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                error_code = error_data.get("error", {}).get("code")
                error_subcode = error_data.get("error", {}).get("error_subcode")
                
                # Check for specific expiry errors
                if error_code == 190 and error_subcode == 463:
                    return {
                        "valid": False,
                        "status": "expired",
                        "error_code": error_code,
                        "error_subcode": error_subcode,
                        "error_message": error_message,
                        "message": "Token has expired - needs regeneration"
                    }
                elif error_code == 190:
                    return {
                        "valid": False,
                        "status": "invalid",
                        "error_code": error_code,
                        "error_subcode": error_subcode,
                        "error_message": error_message,
                        "message": "Token is invalid"
                    }
                else:
                    return {
                        "valid": False,
                        "status": "error",
                        "error_code": error_code,
                        "error_subcode": error_subcode,
                        "error_message": error_message,
                        "message": f"Token validation failed: {error_message}"
                    }
                    
        except requests.exceptions.Timeout:
            return {
                "valid": False,
                "status": "timeout",
                "error_message": "Request timeout - check network connectivity",
                "message": "Token validation timed out"
            }
        except requests.exceptions.ConnectionError:
            return {
                "valid": False,
                "status": "network_error",
                "error_message": "Network connection failed",
                "message": "Unable to connect to Meta API"
            }
        except Exception as e:
            return {
                "valid": False,
                "status": "exception",
                "error_message": str(e),
                "message": f"Token validation error: {str(e)}"
            }
    
    def get_token_status_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive token status for user
        """
        config = self.db.query(OfficialWhatsAppConfig).filter(
            OfficialWhatsAppConfig.busi_user_id == user_id
        ).first()
        
        if not config:
            return {
                "has_config": False,
                "message": "No official WhatsApp configuration found"
            }
        
        # Validate token
        validation_result = self.validate_token(config)
        
        return {
            "has_config": True,
            "config_id": config.id,
            "business_number": config.business_number,
            "waba_id": config.waba_id,
            "phone_number_id": config.phone_number_id,
            "is_active": config.is_active,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
            "token_validation": validation_result,
            "recommendations": self._get_recommendations(validation_result)
        }
    
    def _get_recommendations(self, validation_result: Dict[str, Any]) -> list:
        """Get recommendations based on validation result"""
        recommendations = []
        
        if not validation_result.get("valid", False):
            status = validation_result.get("status", "")
            
            if status == "expired":
                recommendations.extend([
                    "🔄 Regenerate access token from Meta Developer Dashboard",
                    "📱 Go to https://developers.facebook.com/apps",
                    "🔑 Select your app and generate new System User Token",
                    "⚠️ Use Permanent System User Token for long-term access",
                    "🔄 Update token in database after regeneration"
                ])
            elif status == "invalid":
                recommendations.extend([
                    "❌ Token is invalid - check token format",
                    "🔄 Generate new token from Meta Developer Dashboard",
                    "✅ Ensure token has required permissions: whatsapp_business_messaging"
                ])
            elif status in ["timeout", "network_error"]:
                recommendations.extend([
                    "🌐 Check internet connection",
                    "🔧 Verify Meta API accessibility",
                    "🔄 Try again after checking network"
                ])
        else:
            recommendations.extend([
                "✅ Token is valid and active",
                "📊 Monitor token expiry regularly",
                "🔄 Consider setting up token expiry alerts",
                "📱 Use Permanent System User Token for production"
            ])
        
        return recommendations
    
    def check_all_user_tokens(self) -> Dict[str, Any]:
        """
        Check token status for all users (admin function)
        """
        configs = self.db.query(OfficialWhatsAppConfig).all()
        
        results = {
            "total_configs": len(configs),
            "valid_tokens": 0,
            "expired_tokens": 0,
            "invalid_tokens": 0,
            "error_tokens": 0,
            "user_details": []
        }
        
        for config in configs:
            validation = self.validate_token(config)
            
            user_detail = {
                "busi_user_id": config.busi_user_id,
                "business_number": config.business_number,
                "phone_number_id": config.phone_number_id,
                "is_active": config.is_active,
                "token_status": validation.get("status", "unknown"),
                "token_valid": validation.get("valid", False),
                "error_message": validation.get("error_message"),
                "recommendations": self._get_recommendations(validation)
            }
            
            results["user_details"].append(user_detail)
            
            # Count statuses
            if validation.get("valid", False):
                results["valid_tokens"] += 1
            else:
                status = validation.get("status", "")
                if status == "expired":
                    results["expired_tokens"] += 1
                elif status == "invalid":
                    results["invalid_tokens"] += 1
                else:
                    results["error_tokens"] += 1
        
        return results
    
    def update_token(self, user_id: str, new_token: str) -> Dict[str, Any]:
        """
        Update access token for user
        """
        config = self.db.query(OfficialWhatsAppConfig).filter(
            OfficialWhatsAppConfig.busi_user_id == user_id
        ).first()
        
        if not config:
            return {
                "success": False,
                "message": "No configuration found for user"
            }
        
        # Validate new token before updating
        old_token = config.access_token
        config.access_token = new_token
        
        validation = self.validate_token(config)
        
        if validation.get("valid", False):
            self.db.commit()
            logger.info(f"✅ Token updated successfully for user {user_id}")
            return {
                "success": True,
                "message": "Token updated and validated successfully",
                "validation": validation
            }
        else:
            # Rollback on invalid token
            config.access_token = old_token
            self.db.rollback()
            logger.warning(f"❌ New token validation failed for user {user_id}")
            return {
                "success": False,
                "message": "New token validation failed",
                "validation": validation
            }

# Global functions for easy access
def get_token_service(db: Session) -> TokenService:
    """Get token service instance"""
    return TokenService(db)

def validate_user_token(db: Session, user_id: str) -> Dict[str, Any]:
    """Validate token for specific user"""
    service = TokenService(db)
    return service.get_token_status_summary(user_id)
