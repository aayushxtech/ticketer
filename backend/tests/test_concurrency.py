"""
Concurrency Tests — prove that the system prevents double-booking under
parallel requests.

---------------------------------------------------------------------------
WHAT IS THE RACE CONDITION WE'RE TESTING?
---------------------------------------------------------------------------
Two (or more) users submit booking requests for the SAME seat at the SAME
time.  In a naive system with no locking:

  Thread 1: reads seat → is_booked = False
  Thread 2: reads seat → is_booked = False   (stale!)
  Thread 1: writes seat → is_booked = True
  Thread 2: writes seat → is_booked = True   ← DOUBLE BOOKING!

Both threads see the seat as unbooked, both succeed, and the seat is
"sold" twice.  This is a Time-of-Check to Time-of-Use (TOCTOU) bug.

---------------------------------------------------------------------------
WHY NAIVE SYSTEMS FAIL
---------------------------------------------------------------------------
Without a locking mechanism, the read and write are not atomic.  The gap
between reading `is_booked` and writing `is_booked = True` allows another
thread to slip in and read the stale value.

---------------------------------------------------------------------------
HOW OUR BACKEND PREVENTS IT
---------------------------------------------------------------------------
Our booking service uses an ATOMIC conditional UPDATE:
    UPDATE seats SET is_booked = True
    WHERE id IN (:ids) AND show_id = :sid AND is_booked = False

This is a single SQL statement — there is no gap between "check" and
"update".  The database engine guarantees atomicity of the statement.

If two threads execute this simultaneously for the same seat:
  - Thread A's UPDATE matches (is_booked = False) → sets to True, rowcount=1
  - Thread B's UPDATE does NOT match (is_booked = True now) → rowcount=0
  - Thread B sees rowcount != expected → rolls back → returns failure

SQLite's database-level write lock further serialises the UPDATEs, so
only one can execute at a time anyway.

---------------------------------------------------------------------------
SQLITE CONCURRENCY LIMITATIONS
---------------------------------------------------------------------------
• SQLite serialises ALL writes — not just writes to the same row.  This
  means two bookings for DIFFERENT seats also serialise, reducing throughput.

• Under heavy concurrent load, blocked threads may hit SQLITE_BUSY timeouts.

• For production with high concurrency, PostgreSQL (which has true row-level
  locking via MVCC + SELECT FOR UPDATE) is strongly recommended.

For this small system, SQLite's serialised writes + atomic conditional
UPDATE are sufficient and correct.
---------------------------------------------------------------------------
"""

from concurrent.futures import ThreadPoolExecutor, as_completed


class TestConcurrentBooking:
    """
    Simulate multiple users trying to book the SAME seat at the same time.

    We use ThreadPoolExecutor to fire N parallel requests through the
    TestClient, then verify:
      - Exactly ONE request succeeds (200)
      - All others fail (409)
      - The seat is booked exactly once in the DB
    """

    def test_five_threads_same_seat(self, client, sample_show):
        """
        5 concurrent threads all try to book the SAME seat.
        Only 1 should succeed; the other 4 should get 409.
        """
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        target_seat_id = seats[0]["id"]

        results = []

        def _attempt():
            """Each thread makes its own independent booking request."""
            resp = client.post(
                "/book",
                json={"show_id": show_id, "seat_ids": [target_seat_id]},
            )
            return resp.status_code

        # ------------------------------------------------------------------
        # Fire 5 threads simultaneously
        # ------------------------------------------------------------------
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(_attempt) for _ in range(5)]
            for future in as_completed(futures):
                results.append(future.result())

        # ------------------------------------------------------------------
        # Assertions
        # ------------------------------------------------------------------
        successes = results.count(200)
        failures = results.count(409)

        assert successes == 1, (
            f"Expected exactly 1 success, got {successes}. "
            f"Results: {results}"
        )
        assert failures == 4, (
            f"Expected 4 failures (409), got {failures}. "
            f"Results: {results}"
        )

        # Verify final DB state: the seat must be booked
        updated_seats = client.get(f"/shows/{show_id}/seats").json()
        target = next(s for s in updated_seats if s["id"] == target_seat_id)
        assert target["is_booked"] is True

    def test_ten_threads_same_seat(self, client, sample_show):
        """
        10 concurrent threads booking the same seat.
        Stress test: exactly 1 success, 9 failures.
        """
        show_id = sample_show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        target_seat_id = seats[0]["id"]

        results = []

        def _attempt():
            resp = client.post(
                "/book",
                json={"show_id": show_id, "seat_ids": [target_seat_id]},
            )
            return resp.status_code

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_attempt) for _ in range(10)]
            for future in as_completed(futures):
                results.append(future.result())

        successes = results.count(200)
        assert successes == 1, f"Expected 1 success, got {successes}. Results: {results}"

        # Verify seat is booked exactly once
        updated = client.get(f"/shows/{show_id}/seats").json()
        target = next(s for s in updated if s["id"] == target_seat_id)
        assert target["is_booked"] is True

    def test_concurrent_different_seats_all_succeed(self, client):
        """
        5 threads each booking a DIFFERENT seat — all should succeed.
        This verifies that our locking doesn't over-reject.
        """
        # Create a show with 5 seats
        show = client.post(
            "/admin/create-show",
            json={
                "name": "Different Seats Test",
                "datetime": "2026-10-01T18:00:00",
                "total_seats": 5,
            },
        ).json()
        show_id = show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()

        results = []

        def _book_one(seat_id):
            resp = client.post(
                "/book",
                json={"show_id": show_id, "seat_ids": [seat_id]},
            )
            return resp.status_code

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [
                pool.submit(_book_one, seats[i]["id"])
                for i in range(5)
            ]
            for future in as_completed(futures):
                results.append(future.result())

        successes = results.count(200)
        assert successes == 5, (
            f"All 5 different-seat bookings should succeed, got {successes}. "
            f"Results: {results}"
        )

        # All 5 seats should be booked
        updated = client.get(f"/shows/{show_id}/seats").json()
        for seat in updated:
            assert seat["is_booked"] is True

    def test_concurrent_overlapping_multi_seat_booking(self, client):
        """
        Two threads try to book overlapping sets of seats:
          Thread A: seats [1, 2, 3]
          Thread B: seats [2, 3, 4]

        Seats 2 and 3 overlap.  Only one request should fully succeed.
        The other must fail (no partial booking due to atomicity).
        """
        show = client.post(
            "/admin/create-show",
            json={
                "name": "Overlap Test",
                "datetime": "2026-11-01T18:00:00",
                "total_seats": 5,
            },
        ).json()
        show_id = show["id"]
        seats = client.get(f"/shows/{show_id}/seats").json()
        ids = [s["id"] for s in seats]

        results = []

        def _book_set(seat_ids):
            resp = client.post(
                "/book",
                json={"show_id": show_id, "seat_ids": seat_ids},
            )
            return resp.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(_book_set, [ids[0], ids[1], ids[2]])
            future_b = pool.submit(_book_set, [ids[1], ids[2], ids[3]])
            results = [future_a.result(), future_b.result()]

        successes = results.count(200)
        failures = results.count(409)

        # Exactly one succeeds, the other fails
        assert successes == 1, f"Expected 1 success, got {successes}. Results: {results}"
        assert failures == 1, f"Expected 1 failure, got {failures}. Results: {results}"
