import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check main.py fixes
try:
    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    has_timeout = 'asyncio.wait_for' in main_content and 'timeout=30.0' in main_content
    has_timeout_error = 'asyncio.TimeoutError' in main_content
    logger.info('main.py timeout fix: YES' if has_timeout and has_timeout_error else 'main.py timeout fix: NO')
except Exception as e:
    logger.error(f'Error checking main.py: {e}')

# Check google_sheets.py fixes
try:
    with open('api/google_sheets.py', 'r', encoding='utf-8') as f:
        gs_content = f.read()
    
    has_timeout = 'asyncio.wait_for' in gs_content and 'timeout=10.0' in gs_content
    has_reduced_retries = 'max_retries = 2' in gs_content
    has_timeout_handling = 'asyncio.TimeoutError' in gs_content
    logger.info('google_sheets.py timeout fix: YES' if has_timeout else 'google_sheets.py timeout fix: NO')
    logger.info('google_sheets.py reduced retries: YES' if has_reduced_retries else 'google_sheets.py reduced retries: NO')
    logger.info('google_sheets.py timeout handling: YES' if has_timeout_handling else 'google_sheets.py timeout handling: NO')
except Exception as e:
    logger.error(f'Error checking google_sheets.py: {e}')

# Check SessionStatus fix
try:
    with open('services/whatsapp_engine_service.py', 'r', encoding='utf-8') as f:
        service_content = f.read()
    
    has_fix = 'SessionStatus.disconnected' in service_content and 'SessionStatus.DISCONNECTED' not in service_content
    logger.info('SessionStatus fix: YES' if has_fix else 'SessionStatus fix: NO')
except Exception as e:
    logger.error(f'Error checking whatsapp_engine_service.py: {e}')

# Check trigger history
try:
    from db.session import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        result = db.execute(text('SELECT COUNT(*) FROM sheet_trigger_history'))
        count = result.scalar()
        logger.info(f'Trigger history records: {count}')
        logger.info('Trigger history clean: YES' if count == 0 else 'Trigger history clean: NO')
    finally:
        db.close()
except Exception as e:
    logger.error(f'Error checking trigger history: {e}')
