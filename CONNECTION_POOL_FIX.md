# Database Connection Pool Exhaustion Fix

## Problem
The application was experiencing connection pool exhaustion errors:
```
QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
```

## Root Cause
The database engine was created with SQLAlchemy's default pool settings (pool_size=5, max_overflow=10) instead of the configured settings (pool_size=20, max_overflow=20). This happened because:

1. The engine is cached in `settings._engine` 
2. After config changes, the cached engine with old settings persisted
3. The server wasn't restarted to pick up new pool settings

## Solution

### 1. Added Pool Settings Logging (config.py)
- Added logging when engine is created to show actual pool settings
- This helps verify that the correct settings are being applied

### 2. Added Engine Recreation Method (config.py)
- Added `recreate_engine()` method to force disposal and recreation of the engine
- This allows fixing pool issues without full server restart

### 3. Enhanced Health Check (main.py)
- Added pool status to `/health/db` endpoint
- Shows: size, checked_in, checked_out, overflow, configured values
- Helps diagnose pool exhaustion issues

### 4. Added Admin Recreate Endpoint (main.py)
- Added `POST /admin/db/recreate-engine` endpoint
- Forces engine recreation with new pool settings
- Updates all references (db.base.engine, SessionLocal)

## How to Fix

### Option 1: Restart Server (Recommended)
```bash
# Stop the server and restart it
# This will create a new engine with correct pool settings
```

### Option 2: Use Admin Endpoint (Without Restart)
```bash
# Call the admin endpoint to recreate the engine
curl -X POST http://localhost:8000/admin/db/recreate-engine
```

### Option 3: Check Pool Status
```bash
# Check current pool status
curl http://localhost:8000/health/db
```

## Configuration
Current pool settings in `core/config.py`:
- `DATABASE_POOL_SIZE: int = 20`
- `DATABASE_MAX_OVERFLOW: int = 20`
- Total max connections: 40

## Verification
After applying the fix, check the logs for:
```
🔧 Database engine created with pool_size=20, max_overflow=20
```

And verify pool status via `/health/db` endpoint shows correct configured values.

## Prevention
To prevent this in the future:
1. Always restart the server after changing pool settings
2. Monitor pool status via `/health/db` endpoint regularly
3. Consider adding alerts for pool exhaustion
