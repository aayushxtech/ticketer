"""
Booking Service — Business logic for concurrent seat booking.

This module contains the core booking function that handles:
  1. Seat validation
  2. Concurrency-safe atomic booking
  3. Commit-or-rollback guarantee

---------------------------------------------------------------------------
WHAT IS A RACE CONDITION? (Double-booking problem)
---------------------------------------------------------------------------
Imagine two users (Alice & Bob) try to book Seat #5 at the same time:

  NAIVE (broken) approach:
    1. Alice reads Seat #5 → is_booked = False  ✓
    2. Bob   reads Seat #5 → is_booked = False  ✓   (same stale data!)
    3. Alice sets  Seat #5 → is_booked = True   ✓
    4. Bob   sets  Seat #5 → is_booked = True   ✓   ← DOUBLE BOOKING!

Both users believe they booked the seat. The last write wins and there is
no error — even though the seat was sold twice.

WHY THE NAIVE APPROACH FAILS:
  The read and write happen in separate steps with no mutual exclusion.
  Between Alice's read and write, Bob can also read the old value. This
  is a classic Time-of-Check to Time-of-Use (TOCTOU) race condition.

---------------------------------------------------------------------------
HOW WE PREVENT DOUBLE BOOKING
---------------------------------------------------------------------------
Instead of the naive read → check → write pattern, we use an ATOMIC
conditional UPDATE:

    UPDATE seats
    SET is_booked = True
    WHERE id IN (:seat_ids)
      AND show_id = :show_id
      AND is_booked = False      ← THIS IS THE KEY

The WHERE clause includes `is_booked = False`.  If two transactions try
to update the same seat concurrently:

  1. Alice's UPDATE matches the row (is_booked = False) and sets it to True.
  2. Bob's UPDATE does NOT match (is_booked is now True), so affected
     rows = 0 for that seat.
  3. We check the affected row count: if it doesn't match the number of
     requested seats, the booking fails and we roll back.

This is a single atomic SQL statement — there is no gap between read and
write, so the TOCTOU race condition is eliminated.

---------------------------------------------------------------------------
SQLITE LIMITATIONS & WHY THIS STILL WORKS
---------------------------------------------------------------------------
• SQLite has NO true row-level locking (unlike PostgreSQL's SELECT FOR
  UPDATE which locks only the requested rows).

• Instead, SQLite uses DATABASE-LEVEL (or page-level in WAL mode) locking:
  – When a write transaction begins, SQLite acquires a RESERVED lock.
  – Any other connection attempting to write will block (or get SQLITE_BUSY)
    until the first transaction finishes.
  – This effectively SERIALISES all write transactions.

• Our atomic UPDATE approach is SQLite-safe because:
  – The UPDATE + WHERE is a single statement executed under SQLite's
    database lock.
  – Even if two connections execute the UPDATE in quick succession, only
    one will find `is_booked = False` and update the row.

• For a small concurrent system this is perfectly adequate:
  – It guarantees correctness (no double-booking).
  – The trade-off is throughput: all writes serialise, not just writes to
    the same row.
  – For a high-throughput system, PostgreSQL + SELECT FOR UPDATE would
    allow multiple non-overlapping seat bookings to proceed in parallel.
---------------------------------------------------------------------------
"""

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Seat
from app.schemas import BookingResponse


def book_seats(db: Session, show_id: int, seat_ids: list[int]) -> BookingResponse:
    """
    Attempt to book the given seats for a show.

    Uses an ATOMIC conditional UPDATE to prevent double-booking:
      UPDATE seats SET is_booked = True
      WHERE id IN (:seat_ids) AND show_id = :show_id AND is_booked = False

    If the affected row count doesn't match the requested count, it means
    some seats were already booked (or don't exist), and we roll back.

    Returns a BookingResponse indicating success or failure.
    """
    try:
        # ------------------------------------------------------------------
        # STEP 1 — Validate: all seat_ids must exist and belong to this show
        # ------------------------------------------------------------------
        # We do a read first to give clear error messages.  This read is
        # NOT the concurrency gate — the UPDATE in step 2 is.
        # ------------------------------------------------------------------
        seats = (
            db.query(Seat)
            .filter(Seat.show_id == show_id, Seat.id.in_(seat_ids))
            .all()
        )

        found_ids = {seat.id for seat in seats}
        missing_ids = set(seat_ids) - found_ids

        if missing_ids:
            db.rollback()
            return BookingResponse(
                success=False,
                booked_seats=[],
                message=f"Seats not found or do not belong to this show: {sorted(missing_ids)}",
            )

        # Check which seats are already booked (for a clear error message)
        already_booked = [s for s in seats if s.is_booked]
        if already_booked:
            booked_numbers = sorted(s.seat_number for s in already_booked)
            db.rollback()
            return BookingResponse(
                success=False,
                booked_seats=[],
                message=f"Seats already booked: {booked_numbers}",
            )

        # ------------------------------------------------------------------
        # STEP 2 — ATOMIC conditional UPDATE (the concurrency gate)
        # ------------------------------------------------------------------
        # This single SQL statement is the concurrency-safe core:
        #   UPDATE seats SET is_booked = True
        #   WHERE id IN (:ids) AND show_id = :sid AND is_booked = False
        #
        # The `is_booked = False` condition ensures that only unbooked seats
        # are updated.  If a concurrent transaction already booked a seat,
        # this UPDATE won't touch it, and `result.rowcount` will be less
        # than expected → we detect the conflict and roll back.
        # ------------------------------------------------------------------
        result = db.execute(
            update(Seat)
            .where(
                Seat.id.in_(seat_ids),
                Seat.show_id == show_id,
                Seat.is_booked == False,  # noqa: E712 — SQLAlchemy filter
            )
            .values(is_booked=True)
        )

        # ------------------------------------------------------------------
        # STEP 3 — Check: did we update ALL requested seats?
        # ------------------------------------------------------------------
        if result.rowcount != len(seat_ids):
            # Some seats were grabbed by another transaction between our
            # read (step 1) and our write (step 2).  Roll back everything
            # to ensure atomicity — no partial bookings.
            db.rollback()
            return BookingResponse(
                success=False,
                booked_seats=[],
                message="Booking conflict: one or more seats were just booked by another user.",
            )

        db.commit()

        booked_numbers = sorted(s.seat_number for s in seats)
        return BookingResponse(
            success=True,
            booked_seats=booked_numbers,
            message=f"Successfully booked {len(seats)} seat(s).",
        )

    except Exception as e:
        # ------------------------------------------------------------------
        # On ANY unexpected error, roll back the transaction to prevent
        # partial writes (e.g. some seats marked booked, others not).
        # ------------------------------------------------------------------
        db.rollback()
        return BookingResponse(
            success=False,
            booked_seats=[],
            message=f"Booking failed due to an internal error: {str(e)}",
        )
