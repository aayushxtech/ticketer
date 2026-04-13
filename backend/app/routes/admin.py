"""
Admin API routes.

Endpoints:
  POST   /admin/create-show    → create a new show + generate seats
  GET    /admin/shows           → list all shows (admin view)
  DELETE /admin/shows/{id}      → delete a show and its seats
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import crud
from app.schemas import ShowCreate, ShowResponse

router = APIRouter(prefix="/admin")


# ---------------------------------------------------------------------------
# POST /admin/create-show
# ---------------------------------------------------------------------------
@router.post("/create-show", response_model=ShowResponse)
def create_show(payload: ShowCreate, db: Session = Depends(get_db)):
    """
    Create a new show and bulk-generate its seats (1 → total_seats).
    Commits atomically — either both the show and all seats are created,
    or nothing is.
    """
    if payload.total_seats <= 0:
        raise HTTPException(status_code=400, detail="total_seats must be greater than 0.")

    try:
        show = crud.create_show(db, payload.name, payload.datetime, payload.total_seats)
        crud.create_seats_bulk(db, show.id, payload.total_seats)
        db.commit()
        db.refresh(show)
        return show
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create show: {str(e)}")


# ---------------------------------------------------------------------------
# GET /admin/shows
# ---------------------------------------------------------------------------
@router.get("/shows", response_model=list[ShowResponse])
def list_shows(db: Session = Depends(get_db)):
    """Return all shows (admin view — same data, different route for clarity)."""
    return crud.get_all_shows(db)


# ---------------------------------------------------------------------------
# DELETE /admin/shows/{show_id}
# ---------------------------------------------------------------------------
@router.delete("/shows/{show_id}")
def remove_show(show_id: int, db: Session = Depends(get_db)):
    """
    Delete a show and all its seats (via cascade).
    Returns a confirmation message.
    """
    show = crud.delete_show(db, show_id)
    if show is None:
        raise HTTPException(status_code=404, detail=f"Show {show_id} not found.")

    db.commit()
    return {"detail": f"Show {show_id} deleted."}
