# Google Sheets Schema Fix - Verification Commands

## 🚀 Quick Fix (Run this first)

```bash
cd "d:\whatsapp api final\whatsapp_platform_backend"
python fix_google_sheets_schema.py
```

## 🔍 Verification Commands

### 1. Check if columns exist after migration
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'google_sheet_triggers' 
AND column_name IN ('webhook_url', 'trigger_config', 'status_column', 'trigger_value')
ORDER BY column_name;
```

### 2. Test with Python (alternative)
```bash
cd "d:\whatsapp api final\whatsapp_platform_backend"
python -c "
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute(\"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'google_sheet_triggers' AND column_name IN ('webhook_url', 'trigger_config', 'status_column', 'trigger_value')\")
print('Columns after migration:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')
conn.close()
"
```

### 3. Verify app startup (no more UndefinedColumn errors)
```bash
cd "d:\whatsapp api final\whatsapp_platform_backend"
python main.py
```

## ✅ Expected Results

After successful migration, you should see:
- `webhook_url`: VARCHAR(255) (nullable)
- `trigger_config`: JSONB (nullable) 
- `status_column`: VARCHAR(100) (default: 'Status')
- `trigger_value`: VARCHAR(100) (default: 'Send')

## 🔄 Safe Restart Process

1. **Stop the app** if running
2. **Run migration**: `python fix_google_sheets_schema.py`
3. **Verify columns**: Use verification commands above
4. **Start app**: `python main.py`
5. **Check logs**: No more `psycopg2.errors.UndefinedColumn` errors

## ⚠️ If Migration Fails

- Check DATABASE_URL in .env file
- Ensure PostgreSQL is accessible
- Verify table exists: `\d google_sheet_triggers`
- Run individual SQL commands from `fix_google_sheets_schema.sql`
