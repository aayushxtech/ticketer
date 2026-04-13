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

  useEffect(() => {
    loadSeats();
  }, [showId]);

  function loadSeats() {
    setLoading(true);
    setStatus({ type: null, message: null });
    getSeats(showId)
      .then(data => {
        setSeats(data);
        setSelectedIds([]);
      })
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
      setStatus({ type: 'success', message: `Successfully booked ${selectedIds.length} seat(s)!` });
      loadSeats();
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    } finally {
      setBooking(false);
    }
  }

  return (
    <div className="booking">
      <div className="booking__header">
        <Link to="/user"><Button variant="secondary">← Back to shows</Button></Link>
      </div>

      <h1 className="booking__title">Select Seats</h1>
      <p className="booking__subtitle">Show #{showId}</p>

      <div className="booking__legend">
        <span className="legend-item"><span className="legend-box legend-box--available" /> Available</span>
        <span className="legend-item"><span className="legend-box legend-box--selected" /> Selected</span>
        <span className="legend-item"><span className="legend-box legend-box--booked" /> Booked</span>
      </div>

      {loading ? (
        <p className="booking__msg">Loading seats…</p>
      ) : (
        <SeatGrid seats={seats} selectedIds={selectedIds} onToggle={toggleSeat} />
      )}

      <StatusMessage type={status.type} message={status.message} />

      <div className="booking__actions">
        <span className="booking__count">
          {selectedIds.length} seat{selectedIds.length !== 1 ? 's' : ''} selected
        </span>
        <Button onClick={handleBook} disabled={selectedIds.length === 0 || booking}>
          {booking ? 'Booking…' : 'Book Seats'}
        </Button>
      </div>
    </div>
  );
}
