# PostgreSQL Database Commands

## Database Connection Info
- **Database**: whatsapp_patform
- **Username**: whatsapp_patform_user
- **Password**: cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm
- **Host**: dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com

## Connection URLs
- **External URL**: postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform
- **Internal URL**: postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a/whatsapp_patform

## Command Line Access (Windows)

### Option 1: Using PGPASSWORD environment variable
```cmd
set PGPASSWORD=cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm
psql -h dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com -U whatsapp_patform_user whatsapp_patform
```

### Option 2: Using password prompt
```cmd
psql -h dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com -U whatsapp_patform_user -d whatsapp_patform -W
```

### Option 3: Full connection string
```cmd
psql "postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform"
```

## Common PostgreSQL Commands

### List all tables
```sql
\dt
```

### Describe table structure
```sql
\d users
\d businesses
\d reseller_analytics
```

### Query users
```sql
SELECT user_id, username, email, role FROM users LIMIT 10;
```

### Check analytics data
```sql
SELECT * FROM reseller_analytics ORDER BY generated_at DESC LIMIT 5;
```

### Count records
```sql
SELECT 
    'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'businesses', COUNT(*) FROM businesses
UNION ALL
SELECT 'reseller_analytics', COUNT(*) FROM reseller_analytics;
```

## Database Backup
```cmd
pg_dump -h dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com -U whatsapp_patform_user whatsapp_patform > backup.sql
```

## Database Restore
```cmd
psql -h dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com -U whatsapp_patform_user whatsapp_patform < backup.sql
```

## Current Tables in Database
- users
- businesses
- credit_distributions
- messages
- devices
- device_sessions
- message_usage_credit_logs
- reseller_analytics
- business_user_analytics
- wo_whatsapp_official_config
