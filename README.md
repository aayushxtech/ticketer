# Ticketer • Concurrency-Safe Booking System

A fast, robust, and minimal full-stack seat booking system built to handle concurrent traffic without breaking a sweat.

**Disclaimer**: This is a "vibe coded" project. It was built rapidly using intuition-driven development—but don't let that fool you. Where it counts (specifically transaction safety and concurrency handling), the engineering is deliberate, strictly layered, and solid. Built fast, but not carelessly.

---

## 🛠 Tech Stack

*   **Frontend**: React (Vite) with a bespoke, minimalistic gray-on-black UI
*   **Backend**: FastAPI (Python)
*   **Database**: SQLite via SQLAlchemy ORM
*   **DevOps**: Docker + Docker Compose

## ✨ Features

### User Actions
*   Browse upcoming shows and events
*   View real-time seating availability on a dynamic graphical grid
*   Select and book multiple seats concurrently 

### Admin Actions
*   Create new shows by specifying date, time, and venue capacity
*   Trigger automatic bulk seat generation for uniform seating layouts
*   Manage existing shows, including physical cascading deletion of stale data

## 🏗 System Design Highlights

*   **Atomic Booking**: The core booking engine bypasses naive read-check-write patterns. It relies on a single-statement atomic transaction (`UPDATE ... WHERE is_booked = False`). You either secure the ticket, or you don't.
*   **Concurrency Safety**: By leaning on database-level constraints and atomic writes, double-booking or TOCTOU (time-of-check to time-of-use) race conditions are mathematically impossible.
*   **Clean Architecture Separation**: The backend strictly segregates concerns. `crud.py` handles pure queries, `services/` encapsulates complex business logic, and `routes/` provides an extremely thin HTTP interface.

---

## 🚀 Running the Project

### Using Docker (Recommended)

Booting the entire stack is single-command simple:

```bash
docker-compose up --build
```
*   Frontend will be available at `http://localhost:5173`
*   Backend API will be running at `http://localhost:8000`

### Local Setup (Manual)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Endpoints

### Public/User
*   `GET /shows` — Fetch all upcoming events
*   `GET /shows/{id}/seats` — Fetch current mapped seating availability
*   `POST /book` — Atomically book an array of seating identifiers

### Admin
*   `POST /admin/create-show` — Register a show and generate seat payloads
*   `GET /admin/shows` — Fetch all shows (Admin view)
*   `DELETE /admin/shows/{id}` — Teardown show and linked seat data

---

## 🧪 Testing

The backend ships with an extensive, 26-case test suite (`pytest`) focusing on data integrity:
1.  **CRUD reliability**: Confirms database read/write safety and cascade deletions.
2.  **Concurrency Testing**: The suite physically blasts the `book` endpoint with concurrent `ThreadPoolExecutor` requests targeting the exact same seat, mathematically proving the atomic locking behavior blocks double-booking.

Run the suite locally:
```bash
cd backend
pytest tests/ -v
```

## 🚧 Limitations

*   **SQLite Locking**: Because SQLite serializes writes at the file level, it safely prevents double-booking but will eventually return `SQLITE_BUSY` timeouts under immense concurrent write load. It's safe, but not infinitely scalable.
*   **Authentication**: Currently omitted to keep the project laser-focused on core concurrency challenges.

## 🔮 Future Improvements

*   Swap SQLite for **PostgreSQL** to unlock row-level pessimistic locking (`SELECT ... FOR UPDATE`), immediately pushing write throughput into enterprise territory.
*   Implement WebSockets to visually lock seats on the frontend grid while a user is entering checkout details.
*   Add token-based authentication (JWT) for the Admin role. 

---

## 🏁 Final Note

This project is proof that balancing rapid velocity and rigorous systems design is entirely achievable. Vibe coding doesn't have to mean sloppy architecture—sometimes it just means writing the boilerplate fast, so you have the time to engineer the hard stuff perfectly.

## 🔗 Contact & Links

*   Author: aayushxtech
