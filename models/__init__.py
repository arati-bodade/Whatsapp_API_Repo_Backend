# Models module - Import order matters for foreign key resolution
from .base import Base

# Import core models first (needed for foreign keys)
from .reseller import Reseller
from .admin import MasterAdmin
from .plan import Plan
from .busi_user import BusiUser
from .device import Device

# Import models that depend on core models
from .credit_distribution import CreditDistribution
from .message import Message
from .device_session import DeviceSession
from .message_usage import MessageUsageCreditLog
from .reseller_analytics import ResellerAnalytics, BusinessUserAnalytics
from .official_whatsapp_config import OfficialWhatsAppConfig, WhatsAppTemplate, WhatsAppWebhookLog

# Import GoogleSheet models last (they depend on BusiUser and Device)
from .google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory

# Import WhatsAppInbox
from .whatsapp_inbox import WhatsAppInbox

# Import QuickReply
from .quick_reply import QuickReply

# Import WhatsAppMessages
from .whatsapp_messages import WhatsAppMessages

# Import Campaign models
from .campaign import Campaign, CampaignDevice, MessageTemplate, MessageLog

# Import AuditLog models
from .audit_log import AuditLog

# Import PaymentOrder
from .payment_order import PaymentOrder

# Import ContactGroup models
from .contact_group import ContactGroup, Contact

# Import ResellerAlert
from .reseller_alert import ResellerAlert

# Import PasswordResetToken
from .password_reset_token import PasswordResetToken

__all__ = [
    "Base", 
    "Reseller", 
    "MasterAdmin", 
    "Plan", 
    "BusiUser", 
    "Device", 
    "CreditDistribution", 
    "Message", 
    "DeviceSession", 
    "MessageUsageCreditLog", 
    "ResellerAnalytics", 
    "BusinessUserAnalytics", 
    "OfficialWhatsAppConfig", 
    "WhatsAppTemplate", 
    "WhatsAppWebhookLog", 
    "GoogleSheet", 
    "GoogleSheetTrigger", 
    "GoogleSheetTriggerHistory", 
    "WhatsAppInbox", 
    "QuickReply", 
    "WhatsAppMessages", 
    "Campaign", 
    "CampaignDevice", 
    "MessageTemplate", 
    "MessageLog", 
    "AuditLog", 
    "PaymentOrder", 
    "ContactGroup", 
    "Contact", 
    "PasswordResetToken", 
    "ResellerAlert"
]
