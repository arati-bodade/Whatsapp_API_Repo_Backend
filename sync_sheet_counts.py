import asyncio
import logging
from sqlalchemy.orm import Session
from db.db_session import SessionLocal
from models.google_sheet import GoogleSheet
from services.google_sheets_service import GoogleSheetsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SYNC_COUNTS")

def sync_all_sheets():
    db = SessionLocal()
    sheets_service = GoogleSheetsService()
    
    try:
        sheets = db.query(GoogleSheet).all()
        logger.info(f"Syncing {len(sheets)} sheets...")
        
        for sheet in sheets:
            try:
                logger.info(f"Syncing sheet: {sheet.sheet_name} ({sheet.spreadsheet_id})")
                rows, _ = sheets_service.get_sheet_data_with_headers(
                    spreadsheet_id=sheet.spreadsheet_id,
                    worksheet_name=sheet.worksheet_name or "Sheet1"
                )
                
                old_count = sheet.total_rows
                new_count = len(rows)
                
                if old_count != new_count:
                    logger.info(f"  Updating row count: {old_count} -> {new_count}")
                    sheet.total_rows = new_count
                else:
                    logger.info(f"  Count is already correct: {new_count}")
                    
            except Exception as e:
                logger.error(f"  Failed to sync sheet {sheet.id}: {e}")
        
        db.commit()
        logger.info("Sync complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    sync_all_sheets()
