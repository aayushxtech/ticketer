import Seat from './Seat';
import './SeatGrid.css';

export default function SeatGrid({ seats, selectedIds, onToggle }) {
  if (!seats || seats.length === 0)
    return <p className="empty">No seats available.</p>;

  const cols = Math.min(seats.length, 10);

  return (
    <div className="seat-grid-wrapper">
      <div className="seat-grid__screen" />
      <span className="seat-grid__screen-label">Screen</span>
      <div
        className="seat-grid"
        style={{ gridTemplateColumns: `repeat(${cols}, 40px)` }}
      >
        {seats.map(seat => {
          let status = 'available';
          if (seat.is_booked) status = 'booked';
          else if (selectedIds.includes(seat.id)) status = 'selected';

          return (
            <Seat
              key={seat.id}
              id={seat.id}
              label={String(seat.seat_number)}
              status={status}
              onToggle={onToggle}
            />
          );
        })}
      </div>
    </div>
  );
}
