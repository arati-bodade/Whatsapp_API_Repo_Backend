-- Migration: Remove device_id from Google Sheet models
-- This migration removes all device-based dependencies from Google Sheet modules
-- and aligns them with Official WhatsApp API architecture

-- Step 1: Drop device_id from google_sheets table
ALTER TABLE google_sheets 
DROP COLUMN IF EXISTS device_id;

-- Step 2: Drop device_id from google_sheet_triggers table  
ALTER TABLE google_sheet_triggers 
DROP COLUMN IF EXISTS device_id;

-- Step 3: Drop device_id from sheet_trigger_history table
ALTER TABLE sheet_trigger_history 
DROP COLUMN IF EXISTS device_id;

-- Step 4: Add official_message_id to sheet_trigger_history for Meta API wamid tracking
ALTER TABLE sheet_trigger_history 
ADD COLUMN IF NOT EXISTS official_message_id VARCHAR(255);

-- Step 5: Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_official_msg_id 
ON sheet_trigger_history(official_message_id);

-- Step 6: Add comments to document the changes
COMMENT ON COLUMN sheet_trigger_history.official_message_id IS 'Meta API message ID (wamid) for official WhatsApp messages';

-- Migration completed successfully
-- All Google Sheet models now use Official WhatsApp Config instead of device-based approach
