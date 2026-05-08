import sys
from services.google_sheets_service import GoogleSheetsService
import logging

logging.basicConfig(level=logging.INFO)

def check_sheet():
    sheets_service = GoogleSheetsService()
    creds = sheets_service.get_service_account_credentials()
    
    spreadsheet_id = "1-6Iv7XupNuV2_o7wZLsrdY4hgEc5ao7TV9IJahju7BE"
    worksheet_name = "Sheet1"
    
    res = sheets_service.get_sheet_data_with_headers(spreadsheet_id, worksheet_name, creds)
    print("Headers:", res[1])
    print("First 2 rows:", res[0][:2])

if __name__ == '__main__':
    check_sheet()
