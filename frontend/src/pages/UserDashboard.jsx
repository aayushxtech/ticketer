import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getShows } from '../services/api';
import './UserDashboard.css';

function ShowCard({ show }) {
  const date = new Date(show.datetime);
  const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  return (
    <Link to={`/user/show/${show.id}`} className="show-card">
      <div className="show-card__icon">🎭</div>
      <div className="show-card__body">
        <h3 className="show-card__name">{show.name}</h3>
        <div className="show-card__meta-row">
          <span className="show-card__meta">📅 {dateStr}</span>
          <span className="show-card__meta">⏰ {timeStr}</span>
          <span className="show-card__meta">💺 {show.total_seats} seats</span>
        </div>
      </div>
      <div className="show-card__arrow">→</div>
    </Link>
  );
}

export default function UserDashboard() {
  const [shows, setShows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getShows()
      .then(setShows)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      {/* Nav */}
      <header className="topnav">
        <span className="topnav__logo">🎟 <span>Ticketer</span></span>
        <Link to="/" className="topnav__back">← Home</Link>
      </header>

      {/* Content */}
      <main className="ud-main">
        <div className="ud-heading">
          <h1 className="ud-heading__title">Upcoming Shows</h1>
          <p className="ud-heading__sub">Select a show to view the seating map and book tickets.</p>
        </div>

        {loading && (
          <div className="ud-state">
            <div className="ud-spinner" />
            <p>Loading shows…</p>
          </div>
        )}

        {error && (
          <div className="ud-state ud-state--error">
            <span>⚠</span>
            <p>Failed to load shows: {error}</p>
          </div>
        )}

        {!loading && !error && shows.length === 0 && (
          <div className="ud-state">
            <span className="ud-state__icon">🎪</span>
            <p>No shows available right now. Check back later!</p>
          </div>
        )}

        {!loading && !error && shows.length > 0 && (
          <div className="ud-list">
            {shows.map(show => (
              <ShowCard key={show.id} show={show} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
