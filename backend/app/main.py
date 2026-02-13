from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import auth, users, services, computers, sessions, transactions, shifts, inventory, expenses, reports, mpesa, print_jobs, customers, invoices, alerts
from .database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Depends
from datetime import datetime

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready CyberCafe POS system with remote management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(services.router)
app.include_router(computers.router)
app.include_router(sessions.router)
app.include_router(transactions.router)
app.include_router(shifts.router)
app.include_router(inventory.router)
app.include_router(expenses.router)
app.include_router(reports.router)
app.include_router(mpesa.router)
app.include_router(print_jobs.router)
app.include_router(customers.router)
app.include_router(invoices.router)
app.include_router(alerts.router)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "CyberCafe POS Pro API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with security validation"""
    from .config import validate_production_config, settings
    
    # CRITICAL: Validate production configuration
    try:
        validate_production_config(settings)
    except RuntimeError as e:
        print(f"\n{e}")
        import sys
        sys.exit(1)  # Exit if validation fails
    
    # Initialize scheduler for anti-theft alerts
    from .services.scheduler import start_scheduler
    start_scheduler()
    
    print(f"\nCyberCafe POS started in {settings.APP_ENV} mode")
    print(f"   Version: {settings.APP_VERSION}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   DEV_BYPASS_AUTH: {settings.DEV_BYPASS_AUTH}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from .services.scheduler import stop_scheduler
    stop_scheduler()


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Enhanced health check endpoint with security info"""
    from .config import settings
    
    try:
        # Check DB connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    # Check scheduler status
    try:
        from .services.scheduler import scheduler
        scheduler_status = "running" if scheduler and scheduler.running else "stopped"
    except:
        scheduler_status = "unknown"
        
    # Check migration status
    try:
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
        from .config import settings as config_settings
        
        # Build path to alembic.ini relative to this file's location
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg_path = os.path.join(base_dir, "alembic.ini")
        
        script = ScriptDirectory(os.path.join(base_dir, "alembic"))
        
        with db.connection() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()
            
            migration_status = "up_to_date" if current_rev == head_rev else f"pending ({current_rev} -> {head_rev})"
    except Exception as e:
        migration_status = f"unknown: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": db_status,
        "scheduler": scheduler_status,
        "migrations": migration_status,
        "server_time": datetime.now().isoformat()
    }
