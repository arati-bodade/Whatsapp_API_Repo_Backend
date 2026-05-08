from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import requests
from urllib.parse import urlencode

from models.official_whatsapp_config import OfficialWhatsAppConfig, WhatsAppTemplate, WhatsAppWebhookLog
from schemas.official_whatsapp_config import (
    OfficialWhatsAppConfigCreate,
    OfficialWhatsAppConfigUpdate,
    WhatsAppAPIResponse,
    WhatsAppWebhookConfig,
    WhatsAppTemplateValidation
)
from services.message_usage_service import MessageUsageService


class OfficialWhatsAppConfigService:
    def __init__(self, db: Session):
        self.db = db
        self.meta_api_base_url = "https://graph.facebook.com/v18.0"
        self.message_usage_service = MessageUsageService(db)

    def _get_error_message(self, response: requests.Response) -> str:
        """Extract a user-friendly error message from Meta API response."""
        try:
            error_data = response.json()
            if isinstance(error_data, dict) and 'error' in error_data:
                error = error_data['error']
                code = error.get('code')
                subcode = error.get('error_subcode')
                message = error.get('message', '')

                # Token Expired (Code 190)
                if code == 190:
                    return "Your Meta Access Token has expired. Please generate a new one in the Meta Developer Portal and update your configuration."
                
                # Invalid Token or permissions
                if code == 100 or code == 10:
                    return f"Meta API Error: {message}. Please check your Access Token and permissions."
                
                # Specific subcode for expired/invalid session
                if subcode == 463 or subcode == 467:
                    return "Your Meta session has expired or the token is invalid. Please update your Access Token."

                return message or response.text
        except Exception:
            pass
        
        return response.text

    def create_config(self, config_data: OfficialWhatsAppConfigCreate) -> OfficialWhatsAppConfig:
        """Create official WhatsApp configuration."""
        db_config = OfficialWhatsAppConfig(
            busi_user_id=config_data.busi_user_id,
            business_number=config_data.whatsapp_official.business_number,
            waba_id=config_data.whatsapp_official.waba_id,
            phone_number_id=config_data.whatsapp_official.phone_number_id,
            access_token=config_data.whatsapp_official.access_token,
            template_status=config_data.whatsapp_official.template_status,
            created_at=config_data.created_at or datetime.now(timezone.utc)
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def get_config_by_user_id(self, busi_user_id: str) -> Optional[OfficialWhatsAppConfig]:
        """Get WhatsApp configuration by user ID."""
        return self.db.query(OfficialWhatsAppConfig).filter(
            OfficialWhatsAppConfig.busi_user_id == busi_user_id
        ).first()

    def update_config(
        self,
        busi_user_id: str,
        config_data: OfficialWhatsAppConfigUpdate
    ) -> Optional[OfficialWhatsAppConfig]:
        """Update WhatsApp configuration."""
        db_config = self.get_config_by_user_id(busi_user_id)
        
        if not db_config:
            return None
        
        update_data = config_data.model_dump(exclude_unset=True)
        
        if "whatsapp_official" in update_data:
            whatsapp_data = update_data["whatsapp_official"]
            for field, value in whatsapp_data.items():
                setattr(db_config, field, value)
        
        if "is_active" in update_data:
            db_config.is_active = update_data["is_active"]
        
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def delete_config(self, busi_user_id: str) -> bool:
        """Delete WhatsApp configuration."""
        db_config = self.get_config_by_user_id(busi_user_id)
        
        if not db_config:
            return False
        
        self.db.delete(db_config)
        self.db.commit()
        return True

    def verify_webhook(self, config: OfficialWhatsAppConfig, webhook_config: WhatsAppWebhookConfig) -> WhatsAppAPIResponse:
        """Verify webhook configuration with Meta API."""
        try:
            url = f"{self.meta_api_base_url}/{config.phone_number_id}/subscribed_apps"
            headers = {
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return WhatsAppAPIResponse(
                    success=True,
                    message="Webhook verified successfully",
                    data=response.json()
                )
            else:
                return WhatsAppAPIResponse(
                    success=False,
                    message="Webhook verification failed",
                    error_code=str(response.status_code),
                    error_message=self._get_error_message(response)
                )
        except Exception as e:
            return WhatsAppAPIResponse(
                success=False,
                message="Webhook verification error",
                error_message=str(e)
            )

    def send_template_message(
        self,
        config: OfficialWhatsAppConfig,
        to_number: str,
        template_name: str,
        template_data: Dict[str, Any],
        language_code: str = "en_US"
    ) -> WhatsAppAPIResponse:
        """Send template message via WhatsApp Cloud API."""
        try:
            url = f"{self.meta_api_base_url}/{config.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code},
                    "components": template_data.get("components", [])
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                api_response = response.json()
                message_id = api_response.get("messages", [{}])[0].get("id")
                
                # 🔥 DEDUCT CREDITS
                try:
                    self.message_usage_service.deduct_credits(
                        busi_user_id=str(config.busi_user_id),
                        message_id=message_id or f"template-{datetime.now().strftime('%H%M%S')}",
                        amount=1
                    )
                except Exception as credit_err:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"⚠️ Credit deduction failed for official template: {str(credit_err)}")

                return WhatsAppAPIResponse(
                    success=True,
                    message="Template message sent successfully",
                    data=api_response
                )
            else:
                error_data = response.json() if response.status_code != 500 else {}
                error_msg = response.text
                
                # 🔥 CUSTOM HANDLING FOR ALLOWED LIST ERROR (131030)
                if isinstance(error_data, dict) and error_data.get('error', {}).get('code') == 131030:
                    error_msg = "Recipient phone number not in allowed list. ACTION REQUIRED: Please add this number to the 'To' field in your Meta Developer Dashboard (WhatsApp > Getting Started) or move to Live mode."

                return WhatsAppAPIResponse(
                    success=False,
                    message="Failed to send template message",
                    error_code=str(response.status_code),
                    error_message=error_msg if error_msg != response.text else self._get_error_message(response)
                )
        except Exception as e:
            return WhatsAppAPIResponse(
                success=False,
                message="Template message sending error",
                error_message=str(e)
            )

    def send_text_message(
        self,
        config: OfficialWhatsAppConfig,
        to_number: str,
        content: str
    ) -> WhatsAppAPIResponse:
        """Send text message via WhatsApp Cloud API."""
        try:
            url = f"{self.meta_api_base_url}/{config.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "recipient_type": "individual",
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": content
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                api_response = response.json()
                message_id = api_response.get("messages", [{}])[0].get("id")

                # 🔥 DEDUCT CREDITS
                try:
                    self.message_usage_service.deduct_credits(
                        busi_user_id=str(config.busi_user_id),
                        message_id=message_id or f"text-{datetime.now().strftime('%H%M%S')}",
                        amount=1
                    )
                except Exception as credit_err:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"⚠️ Credit deduction failed for official text: {str(credit_err)}")

                return WhatsAppAPIResponse(
                    success=True,
                    message="Text message sent successfully",
                    data=api_response
                )
            else:
                error_data = response.json() if response.status_code != 500 else {}
                error_msg = response.text
                
                # 🔥 CUSTOM HANDLING FOR ALLOWED LIST ERROR (131030)
                if isinstance(error_data, dict) and error_data.get('error', {}).get('code') == 131030:
                    error_msg = "Recipient phone number not in allowed list. ACTION REQUIRED: Please add this number to the 'To' field in your Meta Developer Dashboard (WhatsApp > Getting Started) or move to Live mode."
                
                return WhatsAppAPIResponse(
                    success=False,
                    message="Failed to send text message",
                    error_code=str(response.status_code),
                    error_message=error_msg if error_msg != response.text else self._get_error_message(response)
                )
        except Exception as e:
            return WhatsAppAPIResponse(
                success=False,
                message="Text message sending error",
                error_message=str(e)
            )

    def get_business_profile(self, config: OfficialWhatsAppConfig) -> WhatsAppAPIResponse:
        """Get WhatsApp business profile from Meta API."""
        try:
            url = f"{self.meta_api_base_url}/{config.phone_number_id}/whatsapp_business_profile"
            headers = {
                "Authorization": f"Bearer {config.access_token}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return WhatsAppAPIResponse(
                    success=True,
                    message="Business profile retrieved successfully",
                    data=response.json()
                )
            else:
                return WhatsAppAPIResponse(
                    success=False,
                    message="Failed to retrieve business profile",
                    error_code=str(response.status_code),
                    error_message=self._get_error_message(response)
                )
        except Exception as e:
            return WhatsAppAPIResponse(
                success=False,
                message="Business profile retrieval error",
                error_message=str(e)
            )

    def log_webhook_event(self, busi_user_id: str, webhook_event: Dict[str, Any], event_type: str) -> WhatsAppWebhookLog:
        """Log webhook event for processing."""
        webhook_log = WhatsAppWebhookLog(
            busi_user_id=busi_user_id,
            webhook_event=webhook_event,
            event_type=event_type
        )
        
        self.db.add(webhook_log)
        self.db.commit()
        self.db.refresh(webhook_log)
        return webhook_log

    def get_webhook_logs(self, busi_user_id: str, limit: int = 50) -> List[WhatsAppWebhookLog]:
        """Get webhook logs for a user."""
        return self.db.query(WhatsAppWebhookLog).filter(
            WhatsAppWebhookLog.busi_user_id == busi_user_id
        ).order_by(desc(WhatsAppWebhookLog.created_at)).limit(limit).all()

    def validate_template(self, config: OfficialWhatsAppConfig, template_data: WhatsAppTemplateValidation) -> WhatsAppAPIResponse:
        """Validate template with Meta API."""
        try:
            url = f"{self.meta_api_base_url}/{config.waba_id}/message_templates"
            headers = {
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "name": template_data.template_name,
                "category": template_data.category,
                "language": template_data.language,
                "components": []
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return WhatsAppAPIResponse(
                    success=True,
                    message="Template validated successfully",
                    data=response.json()
                )
            else:
                return WhatsAppAPIResponse(
                    success=False,
                    message="Template validation failed",
                    error_code=str(response.status_code),
                    error_message=self._get_error_message(response)
                )
        except Exception as e:
            return WhatsAppAPIResponse(
                success=False,
                message="Template validation error",
                error_message=str(e)
            )

    def sync_templates(self, config: OfficialWhatsAppConfig) -> WhatsAppAPIResponse:
        """Fetch all templates from Meta and sync to DB."""
        try:
            url = f"{self.meta_api_base_url}/{config.waba_id}/message_templates"
            params = {"limit": 100} # Adjust pagination as needed
            headers = {
                "Authorization": f"Bearer {config.access_token}"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                templates_data = data.get("data", [])
                
                synced_count = 0
                for tmpl in templates_data:
                    # Parse interesting fields
                    name = tmpl.get("name")
                    status = tmpl.get("status")
                    category = tmpl.get("category")
                    language = tmpl.get("language")
                    content_str = json.dumps(tmpl.get("components", []))
                    meta_id = tmpl.get("id")

                    # Upsert logic
                    existing = self.db.query(WhatsAppTemplate).filter(
                        WhatsAppTemplate.busi_user_id == config.busi_user_id,
                        WhatsAppTemplate.template_name == name,
                        WhatsAppTemplate.language == language
                    ).first()
                    
                    if existing:
                        existing.template_status = status
                        existing.category = category
                        existing.content = content_str
                        existing.meta_template_id = meta_id
                        existing.updated_at = datetime.now(timezone.utc)
                    else:
                        new_tmpl = WhatsAppTemplate(
                            busi_user_id=config.busi_user_id,
                            template_name=name,
                            template_status=status,
                            category=category,
                            language=language,
                            content=content_str,
                            meta_template_id=meta_id,
                            created_at=datetime.now(timezone.utc)
                        )
                        self.db.add(new_tmpl)
                    synced_count += 1
                
                self.db.commit()
                
                return WhatsAppAPIResponse(
                    success=True,
                    message=f"Synced {synced_count} templates successfully",
                    data={"count": synced_count}
                )
            else:
                return WhatsAppAPIResponse(
                    success=False,
                    message="Failed to fetch templates from Meta",
                    error_code=str(response.status_code),
                    error_message=self._get_error_message(response)
                )

        except Exception as e:
            return WhatsAppAPIResponse(
                success=False,
                message="Template sync error",
                error_message=str(e)
            )

    def get_templates(self, busi_user_id: str) -> List[WhatsAppTemplate]:
        """Get stored templates from DB."""
        return self.db.query(WhatsAppTemplate).filter(
            WhatsAppTemplate.busi_user_id == busi_user_id
        ).all()

    def create_template(self, busi_user_id: str, template_name: str, category: str, language: str, content: str, meta_template_id: str = None) -> WhatsAppTemplate:
        """Create a new template in the database."""
        template = WhatsAppTemplate(
            busi_user_id=busi_user_id,
            template_name=template_name,
            template_status="pending",  # Default status for new templates
            category=category,
            language=language,
            content=content,
            meta_template_id=meta_template_id
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
