import './Card.css';

export default function Card({ children, onClick, className = '' }) {
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag
      className={`card ${onClick ? 'card--clickable' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </Tag>
  );
}
