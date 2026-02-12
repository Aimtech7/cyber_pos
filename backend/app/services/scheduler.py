"""
Background Scheduler for Alert Detection
Uses APScheduler to run alert checks periodically
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.database import SessionLocal
from app.services.alert_engine import run_alert_checks

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def alert_check_job():
    """Job function to run alert checks"""
    logger.info("Running scheduled alert checks...")
    
    db = SessionLocal()
    try:
        alerts = run_alert_checks(db)
        logger.info(f"Alert check completed. Created {len(alerts)} new alerts.")
    except Exception as e:
        logger.error(f"Error running alert checks: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """Initialize and start the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    logger.info("Starting alert detection scheduler...")
    
    scheduler = BackgroundScheduler()
    
    # Run alert checks every 15 minutes
    scheduler.add_job(
        alert_check_job,
        trigger=IntervalTrigger(minutes=15),
        id='alert_checks',
        name='Alert Detection Checks',
        replace_existing=True
    )
    
    # Run daily summary at midnight
    # scheduler.add_job(
    #     daily_summary_job,
    #     trigger=CronTrigger(hour=0, minute=0),
    #     id='daily_summary',
    #     name='Daily Alert Summary',
    #     replace_existing=True
    # )
    
    scheduler.start()
    logger.info("Scheduler started successfully")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped")


def get_scheduler_status():
    """Get current scheduler status"""
    if scheduler is None:
        return {"running": False}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    return {
        "running": True,
        "jobs": jobs
    }
