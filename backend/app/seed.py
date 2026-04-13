"""
Seed script — creates a sample show with seats for quick testing.

Usage:
    cd backend
    source venv/bin/activate
    python -m app.seed

This is idempotent: if the sample show already exists it won't duplicate it.
"""

from app.db import SessionLocal, engine, Base
from app.models import Show, Seat

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # Check if we already seeded
        existing = db.query(Show).filter(Show.name == "Sample Show").first()
        if existing:
            print(f"⚠  Sample show already exists (id={existing.id}). Skipping seed.")
            return

        # Create a show with 20 seats
        show = Show(
            name="Sample Show",
            datetime="2026-05-01T19:00:00",
            total_seats=20,
        )
        db.add(show)
        db.flush()  # Populate show.id before creating seats

        seats = [
            Seat(show_id=show.id, seat_number=i, is_booked=False)
            for i in range(1, show.total_seats + 1)
        ]
        db.add_all(seats)
        db.commit()

        print(f"✅  Created show '{show.name}' (id={show.id}) with {show.total_seats} seats.")
    except Exception as e:
        db.rollback()
        print(f"❌  Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
