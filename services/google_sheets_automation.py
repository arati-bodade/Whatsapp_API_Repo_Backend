#!/usr/bin/env python3
"""
🔥 GOOGLE SHEETS AUTOMATION SERVICE - UNOFFICIAL WHATSAPP API ONLY

This service handles Google Sheet triggers using ONLY Unofficial WhatsApp API.
Completely removes all official WhatsApp logic and uses device-based messaging only.

✅ FEATURES:
- Process triggers using Unofficial WhatsApp devices only
- Send messages via WhatsApp Engine (unofficial)
- Device validation and health checks
- Proper error handling and logging

❌ REMOVED:
- All official WhatsApp API logic
- OfficialWhatsAppConfig dependencies
- OfficialMessageService dependencies
- Template-based messaging logic
"""

# Import the unofficial-only implementation
from .google_sheets_automation_unofficial import GoogleSheetsAutomationServiceUnofficial

# Create alias for backward compatibility
GoogleSheetsAutomationService = GoogleSheetsAutomationServiceUnofficial
