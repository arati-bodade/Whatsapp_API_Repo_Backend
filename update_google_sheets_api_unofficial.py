#!/usr/bin/env python3
"""
Script to update Google Sheets API to use only unofficial WhatsApp
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_google_sheets_api():
    """Update Google Sheets API to use only unofficial WhatsApp"""
    
    logger.info("🔧 UPDATING GOOGLE SHEETS API TO UNOFFICIAL ONLY")
    logger.info("=" * 50)
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'api', 'google_sheets.py')
    
    try:
        # Read the current API file
        with open(api_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logger.info(f"📖 Read {len(lines)} lines from google_sheets.py")
        
        # Create new content by filtering out official-related lines
        new_lines = []
        skip_mode = False
        skip_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip official endpoint definitions
            if '@router.post("/{sheet_id}/official-template-triggers"' in line:
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Skipping official template trigger endpoint (line {i+1})")
                i += 1
                continue
            
            if '@router.get("/official-config/status")' in line:
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Skipping official config status endpoint (line {i+1})")
                i += 1
                continue
            
            if '@router.post("/{sheet_id}/manual-send"' in line and 'OfficialTemplateSendRequest' in lines[i+1]:
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Skipping official manual send endpoint (line {i+1})")
                i += 1
                continue
            
            # Skip official service imports
            if 'from services.google_sheets_official_messaging' in line:
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Skipping official messaging import (line {i+1})")
                i += 1
                continue
            
            if 'from services.official_message_service' in line:
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Skipping official message service import (line {i+1})")
                i += 1
                continue
            
            if 'from services.official_whatsapp_config_service' in line:
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Skipping official config service import (line {i+1})")
                i += 1
                continue
            
            # Skip official schema imports
            if 'OfficialTemplateSendRequest' in line or 'OfficialTemplateSendResponse' in line or 'OfficialTemplateTriggerRequest' in line:
                if 'from schemas.google_sheet import' in lines[max(0, i-5):i+1]:
                    skip_mode = True
                    skip_count += 1
                    logger.info(f"   ✅ Skipping official schema import (line {i+1})")
                    i += 1
                    continue
            
            # Skip official dependency injection functions
            if 'def get_official_' in line:
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Skipping official dependency injection (line {i+1})")
                i += 1
                continue
            
            # If we're in skip mode, look for the end of the function
            if skip_mode:
                # Check if this line ends the function/class
                if line.strip() == '' and i+1 < len(lines) and (lines[i+1].startswith('@') or lines[i+1].startswith('def ') or lines[i+1].startswith('class ') or lines[i+1].startswith('#')):
                    skip_mode = False
                    logger.info(f"   ✅ End of skipped section (line {i+1})")
                i += 1
                continue
            
            # Replace official messaging logic with unofficial-only
            if 'if request.mode == "official":' in line:
                # Find the end of this if block and replace with unofficial logic
                new_lines.append('            # 🔥 UNOFFICIAL ONLY - Always use device-based messaging\n')
                new_lines.append('            if request.mode == "text":\n')
                skip_mode = True
                skip_count += 1
                logger.info(f"   ✅ Replaced official logic with unofficial (line {i+1})")
                i += 1
                continue
            
            # Add the line if we're not skipping
            new_lines.append(line)
            i += 1
        
        # Write the modified content back
        with open(api_file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        logger.info(f"   ✅ Removed {skip_count} official-related sections")
        logger.info("   ✅ API file updated successfully")
        
        logger.info("")
        logger.info("🎉 GOOGLE SHEETS API UPDATED TO UNOFFICIAL ONLY!")
        logger.info("✅ Official WhatsApp endpoints removed")
        logger.info("✅ Official service imports removed")
        logger.info("✅ Official messaging logic replaced with unofficial")
        logger.info("✅ API now uses unofficial devices only")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating Google Sheets API: {e}")
        return False

def main():
    """Main function"""
    success = update_google_sheets_api()
    
    if success:
        logger.info("")
        logger.info("📝 NEXT STEPS:")
        logger.info("1. Restart the backend to apply changes")
        logger.info("2. Test unofficial trigger functionality")
        logger.info("3. Verify official endpoints are no longer accessible")
        logger.info("4. Test trigger execution with devices only")
    else:
        logger.error("❌ Failed to update Google Sheets API - please check the error above")

if __name__ == "__main__":
    main()
