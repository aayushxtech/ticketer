"""
Pydantic schemas for request validation and response serialization.

These define the API contract between frontend and backend.
"""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Show
# ---------------------------------------------------------------------------
class ShowCreate(BaseModel):
    """Request body for POST /admin/create-show."""
    name: str
    datetime: str       # ISO-8601 string, e.g. "2026-05-01T19:00:00"
    total_seats: int


class ShowResponse(BaseModel):
    """Response shape for a single show."""
    id: int
    name: str
    datetime: str
    total_seats: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Seat
# ---------------------------------------------------------------------------
class SeatResponse(BaseModel):
    """Response shape for a single seat."""
    id: int
    seat_number: int
    is_booked: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------
class BookingRequest(BaseModel):
    """Request body for POST /book."""
    show_id: int
    seat_ids: list[int]


class BookingResponse(BaseModel):
    """Response shape for a booking attempt."""
    success: bool
    booked_seats: list[int]
    message: str
