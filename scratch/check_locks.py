from db.session import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LOCK_CHECK")

def check_db_locks():
    session = SessionLocal()
    try:
        logger.info("🔍 Checking for database locks and active sessions...")
        
        # 1. Total active sessions
        sessions_query = text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
        active_sessions = session.execute(sessions_query).scalar()
        logger.info(f"📊 Active sessions: {active_sessions}")
        
        # 2. Idle in transaction (The silent killers)
        idle_in_tx_query = text("SELECT pid, usename, query, state_change FROM pg_stat_activity WHERE state = 'idle in transaction'")
        idle_in_tx = session.execute(idle_in_tx_query).fetchall()
        logger.info(f"📊 Idle in transaction sessions: {len(idle_in_tx)}")
        for pid, user, query, change in idle_in_tx:
            logger.warning(f"   ⚠️ PID {pid} ({user}) is idle in transaction since {change}. Last query: {query[:100]}")
            
        # 3. Blocking locks
        locks_query = text("""
            SELECT 
                blocked_locks.pid AS blocked_pid,
                blocking_locks.pid AS blocking_pid,
                blocked_activity.query AS blocked_query,
                blocking_activity.query AS blocking_query
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_locks.pid = blocked_activity.pid
            JOIN pg_catalog.pg_locks blocking_locks 
                ON blocking_locks.locktype = blocked_locks.locktype
                AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
                AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                AND blocking_locks.pid != blocked_locks.pid
            JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_locks.pid = blocking_activity.pid
            WHERE NOT blocked_locks.GRANTED;
        """)
        blocking = session.execute(locks_query).fetchall()
        if blocking:
            logger.error(f"🚨 FOUND {len(blocking)} BLOCKING LOCKS!")
            for b_pid, blk_pid, b_q, blk_q in blocking:
                logger.error(f"   ⛓️ PID {b_pid} is BLOCKED by PID {blk_pid}")
                logger.error(f"   ⛓️ Blocked Query: {b_q[:100]}")
                logger.error(f"   ⛓️ Blocking Query: {blk_q[:100]}")
        else:
            logger.info("✅ No blocking locks found.")
            
    except Exception as e:
        logger.error(f"❌ Error checking locks: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_db_locks()
