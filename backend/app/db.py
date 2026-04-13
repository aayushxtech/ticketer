"""
Database connection setup for the Concurrent Ticket Booking System.

Uses SQLAlchemy with SQLite as the backing store.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Load environment variables from .env file
# ---------------------------------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ticket.db")

# ---------------------------------------------------------------------------
# Engine Configuration
# ---------------------------------------------------------------------------
# WHY `check_same_thread=False`?
#
# SQLite, by default, only allows the thread that created a connection to use
# it.  This is a safety mechanism built into Python's `sqlite3` module (not
# SQLite itself).  FastAPI serves requests across multiple threads via its
# ASGI server (uvicorn), so the thread that opens a connection is rarely the
# same thread that later issues a query.  Setting `check_same_thread=False`
# disables this check so that a single connection can be shared across
# threads.
#
# HOW SQLITE HANDLES CONNECTIONS DIFFERENTLY FROM POSTGRESQL:
#
# • PostgreSQL runs as a separate server process and is designed for many
#   concurrent client connections.  Each connection is isolated and the
#   server serialises writes internally using MVCC.
#
# • SQLite is an embedded, file-based database.  There is no server process.
#   Every read/write goes directly to a single file on disk.  Write
#   operations acquire a file-level lock, meaning only ONE writer can
#   proceed at a time (readers can continue in WAL mode, but writers still
#   serialise).
#
# WHY THIS IS ACCEPTABLE FOR A SMALL CONCURRENT SYSTEM (AND ITS LIMITS):
#
# For a small-to-medium booking system with moderate concurrency, SQLite is
# perfectly fine:
#   – It has zero deployment overhead (no DB server to manage).
#   – Read-heavy workloads perform well.
#   – WAL mode can allow concurrent reads alongside a single writer.
#
# However, it has real limitations:
#   – Only ONE write transaction can execute at a time; others block or
#     receive SQLITE_BUSY.
#   – Under heavy concurrent writes (e.g. hundreds of simultaneous seat
#     bookings) this becomes a bottleneck and can cause timeouts.
#   – There is no row-level locking, so strategies like SELECT … FOR UPDATE
#     (used in PostgreSQL for seat-level pessimistic locking) are not
#     available.
#   – For a production system with high write-concurrency, migrating to
#     PostgreSQL (or another client/server RDBMS) is strongly recommended.
# ---------------------------------------------------------------------------

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
# `autocommit=False` – we control transaction boundaries explicitly.
# `autoflush=False`  – we flush manually to avoid implicit I/O mid-request.
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Declarative base – all ORM models will inherit from this.
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency – yields a DB session per request
# ---------------------------------------------------------------------------
def get_db():
    """
    Dependency generator for FastAPI routes.

    Usage:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session is created at the start of a request and closed when the
    request finishes (or if an exception occurs), ensuring no leaked
    connections.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
