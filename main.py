print("🚀 [DEV] RELOAD DETECTED - Loading WhatsApp Platform Backend...")
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
from db.base import engine, Base
from db.session import get_db
from sqlalchemy import text
from fastapi import Depends
# Import all models to ensure they're registered with Base.metadata
from models import *
from db.init_db import init_db
from api import (
    reseller_router, business_router, credit_distribution_router,
    devices_router, device_sessions_router, message_usage_router,
    reseller_analytics_router, official_whatsapp_config_router,
    whatsapp_router, user_router, auth_router, google_sheets_router,
    replies_router, token_validation_router, webhooks_router,
    campaigns_router, audit_logs_router, groups_router, quick_replies_router,
    unofficial_public_api_router, official_public_api_router, credits_router, admin_router,
    public_router, me_router, profile_photos_router, reseller_alerts_router
)
from api.ai_support import router as ai_support_router

import uvicorn
import asyncio
import logging
from core.config import settings

class CategoryFilter(logging.Filter):
    """
    🔥 CUSTOM LOGGING FILTER
    Injects default category if missing to prevent KeyError/ValueError
    Makes category OPTIONAL, not mandatory
    """
    def filter(self, record):
        # Set default category if not provided
        if not hasattr(record, 'category'):
            # Use logger name as default category, fallback to GENERAL
            record.category = getattr(record, 'name', 'GENERAL').split('.')[-1].upper()
        
        # Ensure category is always a string
        if record.category and not isinstance(record.category, str):
            record.category = str(record.category)
        
        return True

# Configure structured logging with categories - ROBUST VERSION
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(category)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 🔥 Apply category filter to ALL handlers to handle ALL loggers
category_filter = CategoryFilter()
for handler in logging.root.handlers:
    handler.addFilter(category_filter)

# Create category-specific loggers
db_logger = logging.getLogger("MAIN")

# Force reload
device_logger = logging.getLogger('DEVICE') 
sync_logger = logging.getLogger('SYNC')
engine_logger = logging.getLogger('ENGINE')
qr_logger = logging.getLogger('QR')
session_logger = logging.getLogger('SESSION')

# Reduce noise from third-party libraries
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Global background task references
background_tasks = []

async def keep_engine_alive():
    """Background task to ping WhatsApp Engine every 10 minutes to prevent Render cold starts."""
    from services.engine_keep_alive import initialize_keep_alive
    
    try:
        # Initialize the keep-alive service
        engine_url = settings.WHATSAPP_ENGINE_BASE_URL
        logger.info(f"Starting engine keep-alive service for {engine_url}")
        
        keep_alive_service = initialize_keep_alive(engine_url, ping_interval=600)  # 10 minutes
        
        # Keep the service running in the background
        while True:
            await asyncio.sleep(60)  # Check every minute if service is still running
            
            if not keep_alive_service.running:
                logger.warning("Keep-alive service stopped, restarting...")
                keep_alive_service.start()
                
            # Log status periodically
            status = keep_alive_service.get_status()
            if status["consecutive_failures"] > 0:
                logger.warning(f"Keep-alive status: {status}")
                
    except Exception as e:
        logger.error(f"Failed to start keep-alive service: {str(e)}")
        # Fallback to simple pings if keep-alive service fails
        await _fallback_keep_alive()

async def _fallback_keep_alive():
    """Fallback keep-alive using simple HTTP requests"""
    from services.whatsapp_engine_service import engine_service
    
    logger.info("Using fallback keep-alive method")
    while True:
        try:
            logger.info("PINGING WhatsApp Engine to keep it awake...")
            health = engine_service.check_engine_health()
            if health.get("healthy"):
                logger.info("Engine is awake and healthy")
            else:
                logger.warning(f"Engine ping returned unhealthy: {health.get('error')}")
        except Exception as e:
            logger.error(f"Failed to ping engine: {str(e)}")
        
        # Ping every 10 minutes (Render spins down after 15 mins of inactivity)
        await asyncio.sleep(600)

async def auto_migrate_db():
    """Smartly adds missing columns only if they don't exist."""
    """🚀 [AUTO-HEALER] Smartly adds missing columns only if they don't exist."""
    # Wait for the server to be fully ready (reduced from 5s to 2s for faster startup)
    await asyncio.sleep(2)
    db_logger.info("🛠️ [AUTO-MIGRATE] Checking database synchronization...")
    
    migrations = [
        # (Table, Column, SQL, Description)
        ("campaigns", "scheduled_at", "ALTER TABLE campaigns ADD COLUMN scheduled_at TIMESTAMP WITH TIME ZONE;", "scheduled_at in campaigns"),
        ("google_sheet_triggers", "scheduled_at", "ALTER TABLE google_sheet_triggers ADD COLUMN scheduled_at TIMESTAMP WITH TIME ZONE;", "scheduled_at in triggers"),
        ("google_sheet_triggers", "source_file_url", "ALTER TABLE google_sheet_triggers ADD COLUMN source_file_url TEXT;", "source_file_url in triggers"),
        ("google_sheet_triggers", "user_id", "ALTER TABLE google_sheet_triggers ADD COLUMN user_id VARCHAR(36);", "user_id in triggers"),
        ("google_sheet_triggers", "media_url", "ALTER TABLE google_sheet_triggers ADD COLUMN media_url TEXT;", "media_url in triggers"),
        ("google_sheet_triggers", "media_type", "ALTER TABLE google_sheet_triggers ADD COLUMN media_type VARCHAR(50);", "media_type in triggers"),
    ]
    
    from fastapi.concurrency import run_in_threadpool
    from sqlalchemy.exc import OperationalError
    
    for table, col, sql, desc in migrations:
        try:
            def check_and_run(t, c, s):
                # Use a plain connection instead of a transaction block for checking
                with engine.connect() as conn:
                    # Check if column exists
                    query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name=:t AND column_name=:c;")
                    curr = conn.execute(query, {"t": t, "c": c})
                    if not curr.first():
                        db_logger.info(f"   ➕ Adding missing {c} to {t}...")
                        # Run the migration in its own transaction
                        with engine.begin() as trans_conn:
                            trans_conn.execute(text("SET statement_timeout = '5s';")) # Reduced from 10s to 5s
                            trans_conn.execute(text(s))
                        db_logger.info(f"   ✅ Added {c} to {t}")
            await run_in_threadpool(check_and_run, table, col, sql)
        except OperationalError as oe:
             db_logger.warning(f"   ⚠️ [AUTO-MIGRATE] Connection error during {desc}: {str(oe)[:100]}")
        except Exception as me:
            db_logger.warning(f"   ⚠️ [AUTO-MIGRATE] {desc} skipped: {str(me)[:100]}")

    # Special check for nullable sheet_id
    try:
        def fix_nullable():
            with engine.begin() as conn:
                conn.execute(text("SET statement_timeout = '5s';")) # Reduced from 10s to 5s
                conn.execute(text("ALTER TABLE google_sheet_triggers ALTER COLUMN sheet_id DROP NOT NULL;"))
                conn.execute(text("ALTER TABLE sheet_trigger_history ALTER COLUMN sheet_id DROP NOT NULL;"))
        await run_in_threadpool(fix_nullable)
    except Exception: pass
    
    # Backfill ownership
    try:
        def backfill():
            with engine.begin() as conn:
                conn.execute(text("SET statement_timeout = '5s';")) # Reduced from 10s to 5s
                conn.execute(text("UPDATE google_sheet_triggers t SET user_id = s.user_id FROM google_sheets s WHERE t.sheet_id = s.id AND t.user_id IS NULL;"))
        await run_in_threadpool(backfill)
    except Exception: pass
            
    db_logger.info("✅ [AUTO-MIGRATE] Database synchronization finished")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for safe background task handling"""
    logger.info("🎬 [STARTUP] WhatsApp Platform Backend initializing...")
    logger.info(f"⚙️ [CONFIG] Engine URL (Raw): {settings.WHATSAPP_ENGINE_URL}")
    logger.info(f"⚙️ [CONFIG] Engine URL (Resolved): {settings.WHATSAPP_ENGINE_BASE_URL}")
    
    # 🔥 Log database pool settings for debugging
    logger.info(f"🔧 [DB POOL] Configured pool_size=25, max_overflow=25 (production-optimized)")
    logger.info(f"🔧 [DB POOL] Total max connections=50")
    
    # 1. Run Auto-Migrations in background (to prevent startup hang)
    asyncio.create_task(auto_migrate_db())
    
    # Database initialization disabled as requested
    # try:
    #     logger.info("🗄️ [DB] Initializing database tables and schema...")
    #     from fastapi.concurrency import run_in_threadpool
    #     # Add a timeout to the threadpool task to prevent hanging the whole app
    #     await asyncio.wait_for(run_in_threadpool(init_db), timeout=45.0)
    #     logger.info("✅ [DB] Database initialization complete")
    # except asyncio.TimeoutError:
    #     logger.error("🛑 [DB] Database initialization TIMED OUT after 45s. Check for locks!")
    # except Exception as e:
    #     logger.error(f"❌ [DB] Database initialization FAILED: {e}")
    
    # Start background services
    logger.info("🔄 [SERVICES] Starting background tasks...")
    
    # Schedule campaign tasks
    try:
        from tasks.campaign_tasks import schedule_daily_tasks
        schedule_daily_tasks()
        logger.info("✅ [CAMPAIGNS] Daily tasks scheduled")
    except Exception as e:
        logger.error(f"[CAMPAIGNS] Failed to schedule tasks: {e}")
    
    # Trigger auto-start removed to prevent startup hanging in production
    # Triggers can be manually started via API endpoints if needed
    
    # Keep-alive Engine background task to prevent Render cold starts
    logger.info("Starting engine keep-alive background task...")
    ka_task = asyncio.create_task(keep_engine_alive())
    ka_task.set_name("EngineKeepAlive")
    background_tasks.append(ka_task)
    
    logger.info("[READY] WhatsApp Platform Backend is ready to serve requests")
    yield
    
    # Graceful shutdown
    logger.info("Shutting down WhatsApp Platform Backend...")
    
    # Cancel all background tasks
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
    logger.info("✅ Shutdown completed")

app = FastAPI(
    title="WhatsApp Platform API",
    description="Backend API for WhatsApp Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.53:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "https://whatsapp-platform-api-frontend.onrender.com",
        "https://whatsapp-platform-api-backend.onrender.com",
        "https://whatsapp-platform-api-engine.onrender.com",
    ],
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
logger.info("🔌 [BOOT] Including core routers (reseller, business, credits)...")
app.include_router(reseller_router, prefix="/api/resellers")
app.include_router(business_router, prefix="/api/busi_users")

app.include_router(credit_distribution_router, prefix="/api")
app.include_router(devices_router, prefix="/api/devices")
app.include_router(device_sessions_router, prefix="/api")

# Credits API (v1)
app.include_router(credits_router, prefix="/api/v1/credits")


app.include_router(message_usage_router, prefix="/api/message-usage", tags=["Message Usage & Credit Log"])
app.include_router(reseller_analytics_router, prefix="/api/reseller-analytics", tags=["Reseller Analytics Dashboard"])
app.include_router(official_whatsapp_config_router, prefix="/api/official-whatsapp", tags=["Official WhatsApp Config"])

# Include whatsapp API
app.include_router(whatsapp_router, prefix="/api/whatsapp")


# Include user API (Self-Service)
app.include_router(user_router, prefix="/api/user")


# Include token validation API
app.include_router(token_validation_router, prefix="/api")

# Include auth API
app.include_router(auth_router, prefix="/api/auth")

app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

# Include Reseller Alerts API
app.include_router(reseller_alerts_router, prefix="/api/reseller/alerts", tags=["Reseller Alerts"])

# Include Google Sheets API
logger.info("🔌 [BOOT] Including Google Sheets and automation routers...")
app.include_router(google_sheets_router, prefix="/api/google-sheets")



# 🧨 STEP 5: ADD DEVICE SYNC API
from api.device_sync import router as device_sync_router
app.include_router(device_sync_router, prefix="/api/devices", tags=["Device Sync"])

# 🧨 STEP 6: SETUP ERROR HANDLERS
from api.error_handlers import setup_error_handlers
setup_error_handlers(app)

# Include unofficial public API
logger.info("🔌 [BOOT] Including Public and Webhook routers...")
app.include_router(unofficial_public_api_router, prefix="/api/unofficial", tags=["Unofficial Public API"])

# Include official public API
app.include_router(official_public_api_router, prefix="/api/official", tags=["Official Public API"])


# Include webhooks router
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["Webhooks"])

# Include replies router
app.include_router(replies_router, prefix="/api/replies", tags=["Replies"])


# Include quick replies router
app.include_router(quick_replies_router, prefix="/api/quick-replies", tags=["Quick Replies"])

# Include campaigns API
app.include_router(campaigns_router, prefix="/api/campaign", tags=["Campaign API"])

# Include Audit Logs API
app.include_router(audit_logs_router, prefix="/api/audit-logs", tags=["Audit Logs"])

# Include Groups API
app.include_router(groups_router, prefix="/api/groups", tags=["Groups"])

# Include Public API
from api.public import router as public_router
app.include_router(public_router, prefix="/api/public", tags=["Public"])








# Include Me (Self) API
app.include_router(me_router, prefix="/api")
app.include_router(profile_photos_router, prefix="/api/profile-photos", tags=["Profile Photos"])
app.include_router(ai_support_router, prefix="/api/chatbot", tags=["AI Support"])

# Ensure uploads directory exists
import os
upload_dirs = ["uploads", "uploads/campaign_data", "uploads/trigger_media", "uploads/profile_images"]
for d in upload_dirs:
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WhatsApp Platform Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "WhatsApp Platform Backend"}

@app.get("/api/health/ready")
async def readiness_check():
    """Endpoint for frontend chatbot to check if backend and AI are ready."""
    ai_available = False
    if settings.AI_PROVIDER == "openai":
        ai_available = bool(settings.OPENAI_API_KEY)
    elif settings.AI_PROVIDER == "gemini":
        ai_available = bool(settings.GEMINI_API_KEY)
    elif settings.AI_PROVIDER == "ollama":
        ai_available = True
        
    return {
        "ready": True,
        "ai_available": ai_available
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint to prevent 404 logs."""
    return Response(status_code=204)

@app.get("/health/db")
async def database_health_check(db = Depends(get_db)):
    """Database health check point to verify connection pool health"""
    try:
        db.execute(text("SELECT 1"))
        # 🔥 Log actual pool status
        pool = engine.pool
        checked_out = pool.checkedout()
        total_connections = pool.size() + pool.overflow()
        usage_percent = (checked_out / total_connections * 100) if total_connections > 0 else 0
        
        # Log warning if pool usage is high
        if usage_percent > 80:
            logger.warning(f"⚠️ [DB POOL] High usage: {usage_percent:.1f}% ({checked_out}/{total_connections} connections)")
        elif usage_percent > 60:
            logger.info(f"📊 [DB POOL] Usage: {usage_percent:.1f}% ({checked_out}/{total_connections} connections)")
        
        return {
            "status": "healthy",
            "service": "PostgreSQL Database",
            "pool": {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": checked_out,
                "overflow": pool.overflow(),
                "configured_size": 25,
                "configured_max_overflow": 25,
                "total_max_connections": 50,
                "usage_percent": round(usage_percent, 2)
            }
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})

@app.post("/admin/db/recreate-engine")
async def recreate_database_engine():
    """
    🔥 ADMIN ONLY: Force recreation of database engine with new pool settings
    Use this if connection pool is exhausted or has wrong settings
    """
    try:
        logger.info("🔄 [ADMIN] Forcing database engine recreation...")
        old_engine = engine
        new_engine = settings.recreate_engine()
        
        # Update the global engine reference in db.base
        from db import base
        base.engine = new_engine
        
        # Update sessionmaker
        from db.session import SessionLocal
        SessionLocal.configure(bind=new_engine)
        
        logger.info("✅ [ADMIN] Database engine recreated successfully")
        return {
            "status": "success",
            "message": "Database engine recreated with new pool settings",
            "pool_size": 25,
            "max_overflow": 25
        }
    except Exception as e:
        logger.error(f"❌ [ADMIN] Failed to recreate engine: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})


@app.get("/health/background")
async def background_tasks_health():
    """Check health of background tasks"""
    from api.google_sheets import active_trigger_tasks
    
    task_status = []
    for task in background_tasks:
        status = {
            "name": task.get_name(),
            "done": task.done(),
            "cancelled": task.cancelled(),
            "exception": str(task.exception()) if task.exception() and not task.cancelled() else None
        }
        task_status.append(status)
    
    return {
        "status": "healthy",
        "background_tasks": task_status,
        "total_tasks": len(background_tasks),
        "active_trigger_tasks_count": len(active_trigger_tasks),
        "active_trigger_ids": list(active_trigger_tasks.keys())
    }


@app.get("/test-qr/{device_id}")
async def test_qr_endpoint(device_id: str):
    """Test QR endpoint that bypasses database and directly calls WhatsApp Engine."""
    try:
        import requests
        response = requests.get(f"{settings.WHATSAPP_ENGINE_BASE_URL}/session/{device_id}/qr", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('qr'):
                return {"qr_code": data['qr'], "status": "success"}
            else:
                return {"qr_code": None, "status": data.get('status', 'generating')}
        else:
            return {"error": f"Engine returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}





if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False if os.environ.get("PORT") else True, # Disable reload in production
        log_level="info"
    )


# Reload trigger 3
