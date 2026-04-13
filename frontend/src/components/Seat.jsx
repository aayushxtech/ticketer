import './Seat.css';

export default function Seat({ id, label, status, onToggle }) {
  const isBooked = status === 'booked';
  const isSelected = status === 'selected';

  return (
    <button
      className={`seat seat--${status}`}
      onClick={() => !isBooked && onToggle(id)}
      disabled={isBooked}
      title={isBooked ? 'Booked' : label}
    >
      {label}
    </button>
  );
}
