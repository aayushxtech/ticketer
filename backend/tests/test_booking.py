"""
Booking Logic Tests — validate the booking service via the API.

Tests:
  1. Successful booking → seats marked booked, correct response shape
  2. Double-booking prevention → second attempt fails
  3. Invalid seat IDs → rejection
  4. Mixed case (some booked, some not) → atomic failure (no partial booking)
  5. Empty seat list → 400
  6. Wrong show ID → 404
"""


class TestSuccessfulBooking:
    """Verify that valid booking requests succeed and persist correctly."""

    def test_book_single_seat(self, client, sample_show):
        """Booking a single unbooked seat succeeds."""
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        seat = seats[0]  # First seat

        response = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [seat["id"]]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert seat["seat_number"] in data["booked_seats"]
        assert "message" in data

    def test_book_multiple_seats(self, client, sample_show):
        """Booking multiple unbooked seats at once succeeds."""
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        target_ids = [seats[0]["id"], seats[1]["id"], seats[2]["id"]]

        response = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": target_ids},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["booked_seats"]) == 3

    def test_booked_seats_persist(self, client, sample_show):
        """After booking, seats show is_booked = True when re-fetched."""
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        target_id = seats[0]["id"]
        target_number = seats[0]["seat_number"]

        # Book the seat
        client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [target_id]},
        )

        # Re-fetch and verify
        updated_seats = client.get(f"/shows/{show_id}/seats").json()
        booked_seat = next(s for s in updated_seats if s["id"] == target_id)
        assert booked_seat["is_booked"] is True
        assert booked_seat["seat_number"] == target_number

    def test_booking_response_shape(self, client, sample_show):
        """The booking response has the exact expected fields."""
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()

        response = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [seats[0]["id"]]},
        )
        data = response.json()
        assert "success" in data
        assert "booked_seats" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["booked_seats"], list)
        assert isinstance(data["message"], str)


class TestDoubleBookingPrevention:
    """Verify that booking an already-booked seat fails cleanly."""

    def test_double_book_same_seat(self, client, sample_show):
        """Booking the same seat twice — second attempt must fail with 409."""
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        target_id = seats[0]["id"]

        # First booking — should succeed
        resp1 = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [target_id]},
        )
        assert resp1.status_code == 200
        assert resp1.json()["success"] is True

        # Second booking — same seat — should fail
        resp2 = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [target_id]},
        )
        assert resp2.status_code == 409
        assert "already booked" in resp2.json()["detail"].lower()

    def test_double_book_seat_remains_booked(self, client, sample_show):
        """After a failed double-book attempt, the seat is still booked."""
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        target_id = seats[0]["id"]

        # Book, then try again
        client.post("/book", json={"show_id": show_id, "seat_ids": [target_id]})
        client.post("/book", json={"show_id": show_id, "seat_ids": [target_id]})

        # Verify state
        updated = client.get(f"/shows/{show_id}/seats").json()
        seat = next(s for s in updated if s["id"] == target_id)
        assert seat["is_booked"] is True


class TestInvalidBookingRequests:
    """Verify that bad requests are rejected with correct error codes."""

    def test_invalid_seat_ids(self, client, sample_show):
        """Booking nonexistent seat IDs fails with 409."""
        show_id = sample_show["id"]
        response = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [99999, 99998]},
        )
        assert response.status_code == 409
        assert "not found" in response.json()["detail"].lower()

    def test_empty_seat_ids(self, client, sample_show):
        """Booking with empty seat list fails with 400."""
        show_id = sample_show["id"]
        response = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": []},
        )
        assert response.status_code == 400

    def test_invalid_show_id(self, client):
        """Booking for a nonexistent show fails with 404."""
        response = client.post(
            "/book",
            json={"show_id": 99999, "seat_ids": [1]},
        )
        assert response.status_code == 404

    def test_seats_from_wrong_show(self, client):
        """Booking seats that belong to a different show fails."""
        # Create two shows
        show_a = client.post(
            "/admin/create-show",
            json={"name": "Show A", "datetime": "2026-01-01T00:00:00", "total_seats": 5},
        ).json()
        show_b = client.post(
            "/admin/create-show",
            json={"name": "Show B", "datetime": "2026-01-02T00:00:00", "total_seats": 5},
        ).json()

        # Get seat IDs from show A
        seats_a = client.get(f"/shows/{show_a['id']}/seats").json()
        seat_id_from_a = seats_a[0]["id"]

        # Try to book a Show-A seat under Show B's ID
        response = client.post(
            "/book",
            json={"show_id": show_b["id"], "seat_ids": [seat_id_from_a]},
        )
        assert response.status_code == 409
        assert "not found" in response.json()["detail"].lower()


class TestAtomicBooking:
    """
    Verify that booking is atomic — if ANY seat in the request is already
    booked, the ENTIRE request fails and NO seats are booked (no partial
    booking).
    """

    def test_mixed_booked_and_unbooked_fails_entirely(self, client, sample_show):
        """
        Attempting to book a mix of booked and unbooked seats:
        the entire request must fail, and the unbooked seats must remain
        unbooked (atomicity).
        """
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        seat_a = seats[0]  # Will be pre-booked
        seat_b = seats[1]  # Will remain unbooked

        # Pre-book seat A
        resp = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [seat_a["id"]]},
        )
        assert resp.status_code == 200

        # Attempt to book seat A + seat B together — should fail
        resp = client.post(
            "/book",
            json={"show_id": show_id, "seat_ids": [seat_a["id"], seat_b["id"]]},
        )
        assert resp.status_code == 409

        # Verify seat B is STILL unbooked (atomicity guarantee)
        updated = client.get(f"/shows/{show_id}/seats").json()
        seat_b_updated = next(s for s in updated if s["id"] == seat_b["id"])
        assert seat_b_updated["is_booked"] is False
