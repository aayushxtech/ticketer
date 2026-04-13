"""
CRUD layer — pure database access functions.

Rules:
  • No business logic here — only DB queries and mutations.
  • Every function receives the db session as the first argument.
  • The caller (route or service) is responsible for committing/rolling back.
"""

from sqlalchemy.orm import Session

from app.models import Show, Seat


# ---------------------------------------------------------------------------
# Show operations
# ---------------------------------------------------------------------------
def get_all_shows(db: Session) -> list[Show]:
    """Return all shows, ordered by id."""
    return db.query(Show).order_by(Show.id).all()


def get_show_by_id(db: Session, show_id: int) -> Show | None:
    """Return a single show by primary key, or None if not found."""
    return db.query(Show).filter(Show.id == show_id).first()


def create_show(db: Session, name: str, datetime_str: str, total_seats: int) -> Show:
    """Insert a new show row. Does NOT commit — caller must commit."""
    show = Show(name=name, datetime=datetime_str, total_seats=total_seats)
    db.add(show)
    db.flush()  # Populate show.id so we can use it for seat creation
    return show


def delete_show(db: Session, show_id: int) -> Show | None:
    """
    Delete a show and its seats (via cascade). Returns the deleted show,
    or None if the show_id didn't exist. Does NOT commit.
    """
    show = get_show_by_id(db, show_id)
    if show is None:
        return None
    db.delete(show)
    db.flush()
    return show


# ---------------------------------------------------------------------------
# Seat operations
# ---------------------------------------------------------------------------
def get_seats_by_show(db: Session, show_id: int) -> list[Seat]:
    """Return all seats for a given show, ordered by seat_number."""
    return (
        db.query(Seat)
        .filter(Seat.show_id == show_id)
        .order_by(Seat.seat_number)
        .all()
    )


def create_seats_bulk(db: Session, show_id: int, total_seats: int) -> list[Seat]:
    """
    Bulk-insert seats numbered 1 through total_seats for the given show.
    Uses add_all for efficient batch insertion. Does NOT commit.
    """
    seats = [
        Seat(show_id=show_id, seat_number=i, is_booked=False)
        for i in range(1, total_seats + 1)
    ]
    db.add_all(seats)
    db.flush()
    return seats
