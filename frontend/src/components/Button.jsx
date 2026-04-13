import './Button.css';

export default function Button({ children, onClick, disabled, variant = 'primary', type = 'button' }) {
  return (
    <button
      className={`btn btn--${variant}`}
      onClick={onClick}
      disabled={disabled}
      type={type}
    >
      {children}
    </button>
  );
}
