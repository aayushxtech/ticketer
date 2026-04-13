import './StatusMessage.css';

export default function StatusMessage({ type, message }) {
  if (!message) return null;
  return <div className={`status status--${type}`}>{message}</div>;
}
