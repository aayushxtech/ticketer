"""
Concurrent Ticket Booking System — Application Entry Point.

This module initialises the FastAPI application, creates database tables
on startup, and registers all route modules.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Import models so that SQLAlchemy's Base.metadata knows about all tables
# BEFORE we call create_all().  Without this import the metadata registry
# would be empty and no tables would be created.
# ---------------------------------------------------------------------------
from app.db import engine, Base
from app import models  # noqa: F401 — imported for side-effect (table registration)

# ---------------------------------------------------------------------------
# Import route modules
# ---------------------------------------------------------------------------
from app.routes import user as user_routes
from app.routes import admin as admin_routes

# ---------------------------------------------------------------------------
# Create all tables that are registered on Base.metadata.
# This is a no-op if the tables already exist (SQLite file persists across
# restarts), so it is safe to call on every startup.
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Concurrent Ticket Booking System",
    description="A minimal FastAPI backend for concurrent ticket booking.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the frontend dev server to make requests
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, lock this down to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
app.include_router(user_routes.router)
app.include_router(admin_routes.router)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/")
def health_check():
    """
    Simple liveness probe.
    Returns {"status": "running"} when the server is up.
    """
    return {"status": "running"}
