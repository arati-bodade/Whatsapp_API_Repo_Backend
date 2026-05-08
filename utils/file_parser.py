import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("FILE_PARSER")

def get_recipient_data_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses CSV or Excel file and returns a list of recipient data.
    Automatically identifies the phone column.
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
            
        # Clean dataframe: replace NaN with None for JSON serialization
        df = df.where(pd.notnull(df), None)
        
        # Identify phone column
        phone_col = None
        phone_keywords = ['phone', 'mobile', 'number', 'contact', 'recipient', 'to', 'whatsapp']
        
        # Exact match first
        for col in df.columns:
            if str(col).lower() in phone_keywords:
                phone_col = col
                break
                
        # Partial match if no exact match found
        if not phone_col:
            for col in df.columns:
                for keyword in phone_keywords:
                    if keyword in str(col).lower():
                        phone_col = col
                        break
                if phone_col: break
                
        # Default to first column if no reasonable candidate found
        if not phone_col and not df.empty:
            phone_col = df.columns[0]
            logger.warning(f"Could not reliably identify phone column. Defaulting to: {phone_col}")
            
        if not phone_col:
            return []
            
        formatted_rows = []
        for _, row in df.iterrows():
            actual_phone = row.get(phone_col)
            
            # Skip row if it has no phone number
            if not actual_phone:
                continue
                
            # Basic phone normalization (to string)
            # Remove scientific notation if pandas read it as float
            if isinstance(actual_phone, float):
                actual_phone = str(int(actual_phone))
            else:
                actual_phone = str(actual_phone)
                
            formatted_rows.append({
                "phone": actual_phone,
                "row_data": dict(row)
            })
            
        logger.info(f"Successfully extracted {len(formatted_rows)} recipients from {file_path}")
        return formatted_rows
        
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        raise ValueError(f"Failed to parse data source: {str(e)}")
