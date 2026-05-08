#!/usr/bin/env python3
"""
Check if trigger startup fixes are properly implemented
"""

import logging
import ast
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_main_py_fixes():
    """Check if main.py has the timeout fix"""
    main_file = "main.py"
    if not os.path.exists(main_file):
        logger.error(f"{main_file} not found")
        return False
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check for timeout implementation
    has_timeout = "asyncio.wait_for" in content and "timeout=30.0" in content
    has_timeout_error = "asyncio.TimeoutError" in content
    
    logger.info(f"main.py timeout fix: {'YES' if has_timeout and has_timeout_error else 'NO'}")
    return has_timeout and has_timeout_error

def check_google_sheets_fixes():
    """Check if google_sheets.py has the timeout and retry fixes"""
    gs_file = "api/google_sheets.py"
    if not os.path.exists(gs_file):
        logger.error(f"{gs_file} not found")
        return False
    
    with open(gs_file, 'r') as f:
        content = f.read()
    
    # Check for timeout in trigger startup
    has_timeout = "asyncio.wait_for" in content and "timeout=10.0" in content
    has_reduced_retries = "max_retries = 2" in content
    has_timeout_handling = "asyncio.TimeoutError" in content
    
    logger.info(f"google_sheets.py timeout fix: {'YES' if has_timeout else 'NO'}")
    logger.info(f"google_sheets.py reduced retries: {'YES' if has_reduced_retries else 'NO'}")
    logger.info(f"google_sheets.py timeout handling: {'YES' if has_timeout_handling else 'NO'}")
    
    return has_timeout and has_reduced_retries and has_timeout_handling

def check_session_status_fix():
    """Check if SessionStatus.DISCONNECTED fix is applied"""
    service_file = "services/whatsapp_engine_service.py"
    if not os.path.exists(service_file):
        logger.error(f"{service_file} not found")
        return False
    
    with open(service_file, 'r') as f:
        content = f.read()
    
    # Check for the fix
    has_fix = "SessionStatus.disconnected" in content and "SessionStatus.DISCONNECTED" not in content
    
    logger.info(f"SessionStatus fix: {'YES' if has_fix else 'NO'}")
    return has_fix

def check_trigger_history_clean():
    """Check if trigger history is clean"""
    try:
        from db.session import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            result = db.execute(text('SELECT COUNT(*) FROM sheet_trigger_history'))
            count = result.scalar()
            logger.info(f"Trigger history records: {count}")
            return count == 0
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error checking trigger history: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== VERIFYING BACKEND FIXES ===")
    
    # Check all fixes
    main_ok = check_main_py_fixes()
    gs_ok = check_google_sheets_fixes()
    session_ok = check_session_status_fix()
    history_ok = check_trigger_history_clean()
    
    logger.info("\n=== SUMMARY ===")
    logger.info(f"main.py timeout fix: {'PASS' if main_ok else 'FAIL'}")
    logger.info(f"google_sheets.py fixes: {'PASS' if gs_ok else 'FAIL'}")
    logger.info(f"SessionStatus fix: {'PASS' if session_ok else 'FAIL'}")
    logger.info(f"Trigger history clean: {'PASS' if history_ok else 'FAIL'}")
    
    all_ok = main_ok and gs_ok and session_ok and history_ok
    
    if all_ok:
        logger.info("\n=== ALL FIXES VERIFIED ===")
        logger.info("Backend should now start without hanging")
    else:
        logger.error("\n=== SOME FIXES MISSING ===")
        logger.error("Backend may still have issues")
