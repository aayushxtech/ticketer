"""
User-facing API routes.

Endpoints:
  GET  /shows              → list all shows
  GET  /shows/{id}/seats   → list seats for a show
  POST /book               → book one or more seats
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import crud
from app.schemas import (
    ShowResponse,
    SeatResponse,
    BookingRequest,
    BookingResponse,
)
from app.services.booking_service import book_seats

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /shows
# ---------------------------------------------------------------------------
@router.get("/shows", response_model=list[ShowResponse])
def list_shows(db: Session = Depends(get_db)):
    """Return all shows."""
    return crud.get_all_shows(db)


# ---------------------------------------------------------------------------
# GET /shows/{show_id}/seats
# ---------------------------------------------------------------------------
@router.get("/shows/{show_id}/seats", response_model=list[SeatResponse])
def list_seats(show_id: int, db: Session = Depends(get_db)):
    """Return all seats for a given show."""
    show = crud.get_show_by_id(db, show_id)
    if show is None:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found.")
    return crud.get_seats_by_show(db, show_id)


# ---------------------------------------------------------------------------
# POST /book
# ---------------------------------------------------------------------------
@router.post("/book", response_model=BookingResponse)
def book(request: BookingRequest, db: Session = Depends(get_db)):
    """
    Book one or more seats for a show.

    Delegates to the booking service which handles concurrency-safe
    locking and validation.
    """
    # Quick validation: show must exist
    show = crud.get_show_by_id(db, request.show_id)
    if show is None:
        raise HTTPException(status_code=404, detail=f"Show {request.show_id} not found.")

    if not request.seat_ids:
        raise HTTPException(status_code=400, detail="seat_ids must not be empty.")

    result = book_seats(db, request.show_id, request.seat_ids)

    # If booking failed due to business logic, return 409 Conflict
    if not result.success:
        raise HTTPException(status_code=409, detail=result.message)

    return result
