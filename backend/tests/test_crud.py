"""
CRUD Tests — validate basic database operations via the API.

Tests:
  1. Create a show → data persists correctly
  2. Fetch all shows → returns the right list
  3. Fetch show by ID (via seats endpoint) → correct show
  4. Delete show → show no longer exists
  5. Seat generation → correct count, numbering, and default state
"""


class TestShowCRUD:
    """Test suite for Show create / read / delete operations."""

    def test_create_show(self, client):
        """Creating a show returns the correct data and a valid ID."""
        response = client.post(
            "/admin/create-show",
            json={
                "name": "CRUD Test Show",
                "datetime": "2026-07-01T20:00:00",
                "total_seats": 15,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CRUD Test Show"
        assert data["datetime"] == "2026-07-01T20:00:00"
        assert data["total_seats"] == 15
        assert "id" in data

    def test_fetch_all_shows(self, client, sample_show):
        """GET /shows returns at least the sample show."""
        response = client.get("/shows")
        assert response.status_code == 200
        shows = response.json()
        assert isinstance(shows, list)
        assert len(shows) >= 1
        # The sample show should be in the list
        ids = [s["id"] for s in shows]
        assert sample_show["id"] in ids

    def test_fetch_all_shows_admin(self, client, sample_show):
        """GET /admin/shows returns the same data as GET /shows."""
        response = client.get("/admin/shows")
        assert response.status_code == 200
        shows = response.json()
        assert isinstance(shows, list)
        ids = [s["id"] for s in shows]
        assert sample_show["id"] in ids

    def test_delete_show(self, client):
        """Deleting a show removes it and its seats."""
        # Create a show to delete
        create_resp = client.post(
            "/admin/create-show",
            json={
                "name": "To Be Deleted",
                "datetime": "2026-08-01T18:00:00",
                "total_seats": 5,
            },
        )
        show_id = create_resp.json()["id"]

        # Verify it exists
        seats_resp = client.get(f"/shows/{show_id}/seats")
        assert seats_resp.status_code == 200
        assert len(seats_resp.json()) == 5

        # Delete it
        del_resp = client.delete(f"/admin/shows/{show_id}")
        assert del_resp.status_code == 200
        assert "deleted" in del_resp.json()["detail"].lower()

        # Verify it's gone — seats endpoint should return 404
        seats_resp = client.get(f"/shows/{show_id}/seats")
        assert seats_resp.status_code == 404

    def test_delete_nonexistent_show(self, client):
        """Deleting a show that doesn't exist returns 404."""
        response = client.delete("/admin/shows/99999")
        assert response.status_code == 404

    def test_create_show_invalid_total_seats(self, client):
        """Creating a show with total_seats <= 0 returns 400."""
        response = client.post(
            "/admin/create-show",
            json={
                "name": "Bad Show",
                "datetime": "2026-01-01T00:00:00",
                "total_seats": 0,
            },
        )
        assert response.status_code == 400


class TestSeatGeneration:
    """Test suite for automatic seat generation on show creation."""

    def test_correct_seat_count(self, client, sample_show):
        """Creating a show with N total_seats generates exactly N seat rows."""
        show_id = sample_show["id"]
        response = client.get(f"/shows/{show_id}/seats")
        assert response.status_code == 200
        seats = response.json()
        assert len(seats) == sample_show["total_seats"]

    def test_seat_numbers_sequential(self, client, sample_show):
        """Seat numbers run from 1 to total_seats with no gaps."""
        show_id = sample_show["id"]
        response = client.get(f"/shows/{show_id}/seats")
        seats = response.json()
        seat_numbers = sorted(s["seat_number"] for s in seats)
        expected = list(range(1, sample_show["total_seats"] + 1))
        assert seat_numbers == expected

    def test_all_seats_initially_unbooked(self, client, sample_show):
        """Every seat starts with is_booked = False."""
        show_id = sample_show["id"]
        response = client.get(f"/shows/{show_id}/seats")
        seats = response.json()
        for seat in seats:
            assert seat["is_booked"] is False

    def test_seat_response_shape(self, client, sample_show):
        """Each seat response has the expected keys."""
        show_id = sample_show["id"]
        response = client.get(f"/shows/{show_id}/seats")
        seats = response.json()
        for seat in seats:
            assert "id" in seat
            assert "seat_number" in seat
            assert "is_booked" in seat

    def test_seats_for_nonexistent_show(self, client):
        """Fetching seats for a nonexistent show returns 404."""
        response = client.get("/shows/99999/seats")
        assert response.status_code == 404
