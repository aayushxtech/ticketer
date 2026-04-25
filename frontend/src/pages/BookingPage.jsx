import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getSeats, bookSeats } from '../services/api';
import SeatGrid from '../components/SeatGrid';
import Button from '../components/Button';
import StatusMessage from '../components/StatusMessage';
import './BookingPage.css';

export default function BookingPage() {
  const { showId } = useParams();
  const [seats, setSeats] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [status, setStatus] = useState({ type: null, message: null });

  useEffect(() => { loadSeats(); }, [showId]);

  function loadSeats() {
    setLoading(true);
    setStatus({ type: null, message: null });
    getSeats(showId)
      .then(data => { setSeats(data); setSelectedIds([]); })
      .catch(err => setStatus({ type: 'error', message: err.message }))
      .finally(() => setLoading(false));
  }

  function toggleSeat(id) {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  }

  async function handleBook() {
    if (selectedIds.length === 0) return;
    setBooking(true);
    setStatus({ type: null, message: null });
    try {
      await bookSeats(showId, selectedIds);
      setStatus({ type: 'success', message: `${selectedIds.length} seat${selectedIds.length > 1 ? 's' : ''} booked successfully!` });
      loadSeats();
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    } finally {
      setBooking(false);
    }
  }

  const booked  = seats.filter(s => s.is_booked).length;
  const available = seats.filter(s => !s.is_booked).length;

  return (
    <div className="page">
      {/* Nav */}
      <header className="topnav">
        <span className="topnav__logo">🎟 <span>Ticketer</span></span>
        <Link to="/user" className="topnav__back">← Back to shows</Link>
      </header>

      <main className="bp-main">
        {/* Page title */}
        <div className="bp-heading">
          <h1 className="bp-heading__title">Select Your Seats</h1>
          <p className="bp-heading__sub">Show #{showId}</p>
        </div>

        {/* Stats row */}
        {!loading && (
          <div className="bp-stats">
            <div className="bp-stat">
              <span className="bp-stat__value">{seats.length}</span>
              <span className="bp-stat__label">Total</span>
            </div>
            <div className="bp-stat-divider" />
            <div className="bp-stat">
              <span className="bp-stat__value bp-stat__value--green">{available}</span>
              <span className="bp-stat__label">Available</span>
            </div>
            <div className="bp-stat-divider" />
            <div className="bp-stat">
              <span className="bp-stat__value bp-stat__value--red">{booked}</span>
              <span className="bp-stat__label">Booked</span>
            </div>
            <div className="bp-stat-divider" />
            <div className="bp-stat">
              <span className="bp-stat__value bp-stat__value--accent">{selectedIds.length}</span>
              <span className="bp-stat__label">Selected</span>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="bp-legend">
          <span className="bp-legend-item">
            <span className="bp-legend-box bp-legend-box--available" /> Available
          </span>
          <span className="bp-legend-item">
            <span className="bp-legend-box bp-legend-box--selected" /> Selected
          </span>
          <span className="bp-legend-item">
            <span className="bp-legend-box bp-legend-box--booked" /> Booked
          </span>
        </div>

        {/* Seat grid */}
        {loading ? (
          <div className="bp-loading">
            <div className="ud-spinner" />
            <p>Loading seats…</p>
          </div>
        ) : (
          <SeatGrid seats={seats} selectedIds={selectedIds} onToggle={toggleSeat} />
        )}

        <StatusMessage type={status.type} message={status.message} />

        {/* Actions bar */}
        <div className="bp-actions">
          <span className="bp-actions__count">
            {selectedIds.length > 0
              ? `${selectedIds.length} seat${selectedIds.length > 1 ? 's' : ''} selected`
              : 'No seats selected'}
          </span>
          <Button
            onClick={handleBook}
            disabled={selectedIds.length === 0 || booking}
          >
            {booking ? '⏳ Booking…' : '✓ Confirm Booking'}
          </Button>
        </div>
      </main>
    </div>
  );
}
