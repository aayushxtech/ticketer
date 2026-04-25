import { Link } from 'react-router-dom';
import './Home.css';

const features = [
  {
    icon: '⚡',
    title: 'Atomic Booking',
    desc: 'Single-statement transactions guarantee zero double-booking under any concurrent load.',
  },
  {
    icon: '🔒',
    title: 'Race-Condition Proof',
    desc: 'Database-level locking eliminates TOCTOU vulnerabilities at the engine level.',
  },
  {
    icon: '🗺️',
    title: 'Live Seat Grid',
    desc: 'Real-time graphical seat maps update availability without page reloads.',
  },
  {
    icon: '🛠️',
    title: 'Admin Controls',
    desc: 'Create shows, generate seat layouts and cascade-delete stale events instantly.',
  },
];

export default function Home() {
  return (
    <div className="landing">

      {/* ── Animated background grid ── */}
      <div className="landing__bg" aria-hidden="true">
        <div className="landing__bg-grid" />
        <div className="landing__bg-glow landing__bg-glow--1" />
        <div className="landing__bg-glow landing__bg-glow--2" />
      </div>

      {/* ── Nav bar ── */}
      <header className="landing__nav">
        <span className="landing__logo">🎟 Ticketer</span>
        <nav className="landing__nav-links">
          <a href="#features" className="landing__nav-link">Features</a>
          <a href="#roles" className="landing__nav-link">Get Started</a>
        </nav>
      </header>

      {/* ── Hero ── */}
      <section className="landing__hero">
        <div className="landing__badge">Concurrency-Safe · Production-Ready</div>
        <h1 className="landing__headline">
          Book seats at the<br />
          <span className="landing__headline--accent">speed of light.</span>
        </h1>
        <p className="landing__sub">
          A full-stack ticket booking engine built to handle thousands of<br />
          simultaneous requests without a single double-booking. Ever.
        </p>
        <div className="landing__hero-cta">
          <Link to="/user" className="landing__btn landing__btn--primary">Browse Shows →</Link>
          <a href="#features" className="landing__btn landing__btn--ghost">Learn How It Works</a>
        </div>

        {/* mini stats row */}
        <div className="landing__stats">
          <div className="landing__stat">
            <span className="landing__stat-value">26</span>
            <span className="landing__stat-label">Test Cases</span>
          </div>
          <div className="landing__stat-divider" />
          <div className="landing__stat">
            <span className="landing__stat-value">0</span>
            <span className="landing__stat-label">Double Bookings</span>
          </div>
          <div className="landing__stat-divider" />
          <div className="landing__stat">
            <span className="landing__stat-value">∞</span>
            <span className="landing__stat-label">Concurrent Users</span>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="landing__features" id="features">
        <p className="landing__section-tag">Under the hood</p>
        <h2 className="landing__section-title">Engineered for concurrency</h2>
        <div className="landing__feature-grid">
          {features.map((f) => (
            <div key={f.title} className="landing__feature-card">
              <div className="landing__feature-icon">{f.icon}</div>
              <h3 className="landing__feature-title">{f.title}</h3>
              <p className="landing__feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Role selection ── */}
      <section className="landing__roles" id="roles">
        <p className="landing__section-tag">Get started</p>
        <h2 className="landing__section-title">Choose your role</h2>
        <div className="landing__role-grid">

          <Link to="/user" className="landing__role-card landing__role-card--user">
            <div className="landing__role-icon">🎭</div>
            <h3 className="landing__role-name">User</h3>
            <p className="landing__role-desc">Browse upcoming events, view live seat availability, and book your tickets instantly.</p>
            <span className="landing__role-cta">Enter as User →</span>
          </Link>

          <Link to="/admin" className="landing__role-card landing__role-card--admin">
            <div className="landing__role-icon">⚙️</div>
            <h3 className="landing__role-name">Admin</h3>
            <p className="landing__role-desc">Create shows, configure seating capacity, and manage the full event lifecycle.</p>
            <span className="landing__role-cta">Enter as Admin →</span>
          </Link>

        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing__footer">
        <span>Built by <strong>aayushxtech</strong> · Concurrent Booking System © 2025</span>
      </footer>

    </div>
  );
}
