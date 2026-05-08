#!/usr/bin/env python3
"""
Script to remove official WhatsApp API endpoints from Google Sheets API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def remove_official_endpoints():
    """Remove official WhatsApp API endpoints from google_sheets.py"""
    
    logger.info("🔧 REMOVING OFFICIAL WHATSAPP API ENDPOINTS")
    logger.info("=" * 50)
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'api', 'google_sheets.py')
    
    try:
        # Read the current API file
        with open(api_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"📖 Read {len(content)} characters from google_sheets.py")
        
        # Define patterns to remove official endpoints
        official_patterns = [
            # Remove official template trigger endpoint
            (r'@router\.post\("/\{sheet_id\}/official-template-triggers".*?raise HTTPException\(status_code=500, detail="Failed to create official template trigger"\)', '', re.DOTALL),
            
            # Remove official config status endpoint
            (r'@router\.get\("/official-config/status\).*?raise HTTPException\(status_code=500, detail="Failed to get official config status"\)', '', re.DOTALL),
            
            # Remove official template manual send endpoint
            (r'@router\.post\("/\{sheet_id\}/manual-send".*?raise HTTPException\(status_code=500, detail=f"Failed to send \{request\.mode\} messages"\)', '', re.DOTALL),
            
            # Remove import statements for official services
            (r'from services\.google_sheets_official_messaging import GoogleSheetsOfficialMessagingService\n', ''),
            (r'from services\.official_message_service import OfficialMessageService\n', ''),
            (r'from services\.official_whatsapp_config_service import OfficialWhatsAppConfigService\n', ''),
            
            # Remove dependency injection functions
            (r'def get_official_messaging_service.*?\n\)', '', re.DOTALL),
            (r'def get_official_message_service.*?\n\)', '', re.DOTALL),
            (r'def get_official_config_service.*?\n\)', '', re.DOTALL),
            
            # Remove official schema imports
            (r'    OfficialTemplateSendRequest, OfficialTemplateSendResponse,\n', ''),
            (r'    OfficialTemplateTriggerRequest,\n', ''),
        ]
        
        modified_content = content
        removed_count = 0
        
        # Apply each pattern
        for pattern, replacement in official_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                modified_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                removed_count += len(matches)
                logger.info(f"   ✅ Removed {len(matches)} official endpoint(s) or import(s)")
        
        # Remove official messaging logic from the main messaging endpoint
        official_logic_pattern = r'if request\.mode == "official":.*?else:  # template mode'
        official_matches = re.findall(official_logic_pattern, content, re.DOTALL)
        if official_matches:
            # Replace with unofficial-only logic
            unofficial_replacement = '''# 🔥 UNOFFICIAL ONLY - Always use device-based messaging
            if request.mode == "text":'''
            modified_content = re.sub(official_logic_pattern, unofficial_replacement, modified_content, flags=re.DOTALL)
            removed_count += len(official_matches)
            logger.info(f"   ✅ Removed {len(official_matches)} official messaging logic sections")
        
        # Write the modified content back
        with open(api_file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        logger.info(f"   ✅ Removed {removed_count} official-related sections")
        logger.info("   ✅ API file updated successfully")
        
        # Verify the changes
        with open(api_file_path, 'r', encoding='utf-8') as f:
            updated_content = f.read()
        
        # Check for any remaining official references
        remaining_official = re.findall(r'official', updated_content, re.IGNORECASE)
        if remaining_official:
            logger.warning(f"   ⚠️  Found {len(remaining_official)} remaining 'official' references")
            logger.info("   📝 These may be in comments or legitimate uses")
        else:
            logger.info("   ✅ No 'official' references found")
        
        logger.info("")
        logger.info("🎉 OFFICIAL ENDPOINT REMOVAL COMPLETED!")
        logger.info("✅ Official WhatsApp API endpoints removed")
        logger.info("✅ Official service imports removed")
        logger.info("✅ Official messaging logic removed")
        logger.info("✅ Google Sheets API now uses unofficial devices only")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error removing official endpoints: {e}")
        return False

def main():
    """Main function"""
    success = remove_official_endpoints()
    
    if success:
        logger.info("")
        logger.info("📝 NEXT STEPS:")
        logger.info("1. Restart the backend to apply changes")
        logger.info("2. Test unofficial trigger functionality")
        logger.info("3. Verify official endpoints are no longer accessible")
        logger.info("4. Test trigger execution with devices only")
    else:
        logger.error("❌ Failed to remove official endpoints - please check the error above")

if __name__ == "__main__":
    main()
