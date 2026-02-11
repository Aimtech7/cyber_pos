from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import auth, users, services, computers, sessions, transactions, shifts, inventory, expenses, reports

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


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "CyberCafe POS Pro API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
