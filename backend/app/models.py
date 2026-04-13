"""
SQLAlchemy ORM models for the Concurrent Ticket Booking System.

Tables:
    - shows : Represents a bookable event/show.
    - seats : Represents individual seats belonging to a show.

---------------------------------------------------------------------------
DBMS CONCEPT — NORMALISATION
---------------------------------------------------------------------------
Show and Seat are stored in separate tables (instead of e.g. a JSON blob of
seats inside the show row).  This is **Third Normal Form (3NF)**:

  • Every seat fact (number, booking status) depends on the seat's own
    primary key, not transitively on the show.
  • Eliminates update anomalies — changing a show name doesn't touch seat
    rows, and booking a seat doesn't touch the show row.
  • Enables efficient queries — we can filter/index seats independently
    without scanning or deserialising a parent column.

---------------------------------------------------------------------------
DBMS CONCEPT — CONSTRAINTS (Data Integrity at the DB Level)
---------------------------------------------------------------------------
Constraints are enforced by SQLite itself, not by application code.  This is
critical because:

  • Even if a bug in Python skips a validation check, the DB will reject
    bad data.
  • Concurrent processes that bypass the ORM (e.g. a DB admin or migration
    script) still get integrity protection.

Constraints used here:
  – PRIMARY KEY   : Guarantees row uniqueness and provides a fast lookup
                    index automatically.
  – FOREIGN KEY   : Ensures every seat references a valid show.  Prevents
                    orphan seat rows if a show is deleted (with CASCADE).
  – UNIQUE        : UNIQUE(show_id, seat_number) prevents the same seat
                    number from being inserted twice for the same show.
                    Without this, two concurrent "create show" calls could
                    create duplicate seat rows, leading to double-booking.
  – NOT NULL      : Prevents missing critical data (name, datetime, etc.).

---------------------------------------------------------------------------
DBMS CONCEPT — INDEXING
---------------------------------------------------------------------------
An index on `Seat.show_id` is added explicitly.  Why?

  • The most common query pattern is "get all seats for a given show"
    (`GET /shows/{id}/seats`).  Without an index, SQLite must perform a
    **full table scan** of the seats table for every such request.
  • With the index, SQLite can perform a **B-tree lookup** on `show_id`
    and jump directly to the matching rows — O(log n) instead of O(n).
  • For a show with 100 seats and 10,000 total seat rows across all shows,
    this is the difference between reading 10,000 rows vs ~100 rows.

---------------------------------------------------------------------------
DBMS CONCEPT — FUTURE CONCURRENCY SUPPORT
---------------------------------------------------------------------------
This schema is designed to support concurrency-safe booking later:

  • The `is_booked` boolean on each seat row acts as the **lock target**.
    A booking operation will read `is_booked`, check it is False, then set
    it to True — all within a transaction.

  • In SQLite (serialised writes), only one transaction can write at a time,
    so concurrent bookings are implicitly serialised.  This prevents
    double-booking but can cause SQLITE_BUSY under heavy load.

  • If migrated to PostgreSQL, `SELECT ... FOR UPDATE` (pessimistic locking)
    or optimistic locking with a version column can be added to allow higher
    throughput while still preventing double-booking.
---------------------------------------------------------------------------
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db import Base


# ---------------------------------------------------------------------------
# Show Model
# ---------------------------------------------------------------------------
class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    datetime = Column(String, nullable=False)    # ISO-8601 string for simplicity
    total_seats = Column(Integer, nullable=False)

    # -----------------------------------------------------------------------
    # Relationship: One Show → Many Seats
    # `back_populates` creates a bidirectional link so that:
    #   - show.seats  → list of Seat objects
    #   - seat.show   → the parent Show object
    #
    # `cascade="all, delete-orphan"` means:
    #   - Deleting a show automatically deletes all its seats (no orphans).
    # -----------------------------------------------------------------------
    seats = relationship(
        "Seat",
        back_populates="show",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Show id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Seat Model
# ---------------------------------------------------------------------------
class Seat(Base):
    __tablename__ = "seats"

    # -----------------------------------------------------------------------
    # Table-level constraints
    # -----------------------------------------------------------------------
    # UNIQUE(show_id, seat_number):
    #   Prevents duplicate seat numbers within the same show.  For example,
    #   if show_id=1 already has seat_number=5, attempting to INSERT another
    #   row with (show_id=1, seat_number=5) will raise an IntegrityError.
    #   This is essential because the application creates seats in a loop;
    #   without this constraint, a retry or race condition could silently
    #   create duplicates.
    # -----------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("show_id", "seat_number", name="uq_show_seat"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # -----------------------------------------------------------------------
    # Foreign key to shows.id
    # `index=True` adds a B-tree index on this column.
    #
    # WHY INDEX show_id?
    #   The query `SELECT * FROM seats WHERE show_id = ?` is executed on
    #   every seat-grid load (`GET /shows/{id}/seats`).  An index turns this
    #   from a full table scan into a fast B-tree lookup.  As the seats table
    #   grows, the performance difference becomes significant.
    # -----------------------------------------------------------------------
    show_id = Column(
        Integer,
        ForeignKey("shows.id"),
        nullable=False,
        index=True,
    )

    seat_number = Column(Integer, nullable=False)
    is_booked = Column(Boolean, default=False, nullable=False)

    # -----------------------------------------------------------------------
    # Relationship back to Show
    # -----------------------------------------------------------------------
    show = relationship("Show", back_populates="seats")

    def __repr__(self):
        return (
            f"<Seat id={self.id} show_id={self.show_id} "
            f"seat_number={self.seat_number} booked={self.is_booked}>"
        )
