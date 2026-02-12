from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import auth, users, services, computers, sessions, transactions, shifts, inventory, expenses, reports, mpesa, print_jobs
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


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "CyberCafe POS Pro API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check DB connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        
    return {
        "status": "healthy",
        "version": settings.APP_VERSION if hasattr(settings, "APP_VERSION") else "1.0.0",
        "database": db_status,
        "server_time": datetime.now().isoformat()
    }
