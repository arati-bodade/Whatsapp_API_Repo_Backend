-- Safe PostgreSQL Migration for Google Sheets Triggers
-- Fixes: webhook_url, trigger_config, status_column, trigger_value columns
-- Production-ready with IF NOT EXISTS and proper defaults

-- Add webhook_url column (nullable, safe)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'webhook_url'
    ) THEN
        ALTER TABLE google_sheet_triggers 
        ADD COLUMN webhook_url VARCHAR(255);
        RAISE NOTICE 'Added webhook_url column';
    END IF;
END $$;

-- Add trigger_config column (nullable JSON, safe)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'trigger_config'
    ) THEN
        ALTER TABLE google_sheet_triggers 
        ADD COLUMN trigger_config JSONB;
        RAISE NOTICE 'Added trigger_config column';
    END IF;
END $$;

-- Add status_column column with default (safe)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'status_column'
    ) THEN
        ALTER TABLE google_sheet_triggers 
        ADD COLUMN status_column VARCHAR(100) DEFAULT 'Status';
        
        -- Update existing rows to have the default
        UPDATE google_sheet_triggers 
        SET status_column = 'Status' 
        WHERE status_column IS NULL;
        
        RAISE NOTICE 'Added status_column column with default';
    END IF;
END $$;

-- Add trigger_value column with default (safe)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'trigger_value'
    ) THEN
        ALTER TABLE google_sheet_triggers 
        ADD COLUMN trigger_value VARCHAR(100) DEFAULT 'Send';
        
        -- Update existing rows to have the default
        UPDATE google_sheet_triggers 
        SET trigger_value = 'Send' 
        WHERE trigger_value IS NULL;
        
        RAISE NOTICE 'Added trigger_value column with default';
    END IF;
END $$;

-- Verify all columns exist
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'google_sheet_triggers' 
AND column_name IN ('webhook_url', 'trigger_config', 'status_column', 'trigger_value')
ORDER BY column_name;

-- Migration completed successfully
RAISE NOTICE 'Google Sheets Triggers migration completed successfully!';
