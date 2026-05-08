#!/usr/bin/env python3
"""
📊 GOOGLE SHEET DATA VERIFICATION
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.google_sheets_service import GoogleSheetsService

def verify_google_sheet_data():
    """Verify the Google Sheet data structure"""
    print("📊 VERIFYING GOOGLE SHEET DATA...")
    
    try:
        sheets_service = GoogleSheetsService()
        
        # Test fetching data from the sheet
        rows_data, headers = sheets_service.get_sheet_data_with_headers(
            credentials=None,
            spreadsheet_id="1Cd-YVW119l4yAp3Q5ibnhRcDS0D80nrj8D239F2BUPo",
            worksheet_name="Sheet1"
        )
        
        print(f"   ✅ SUCCESS: Found {len(rows_data)} rows")
        print(f"   📋 Headers: {headers}")
        
        # Display the data
        print("\n   📊 SHEET DATA (First 5 rows):")
        for i, row in enumerate(rows_data[:5]):
            print(f"   Row {i+1}:")
            for key, value in row['data'].items():
                print(f"      {key}: {value}")
            print()
        
        # Extract phone numbers
        phone_numbers = []
        if 'Phone' in headers:
            for row in rows_data:
                phone = row['data'].get('Phone', '')
                if phone:
                    phone_numbers.append(phone)
        
        print(f"   📱 Phone Numbers Found: {phone_numbers}")
        
        return True, rows_data, headers, phone_numbers
        
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return False, None, None, None

if __name__ == "__main__":
    verify_google_sheet_data()
