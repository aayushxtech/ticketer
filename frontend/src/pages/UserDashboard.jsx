import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getShows } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import './UserDashboard.css';

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
    <div className="dashboard">
      <div className="dashboard__header">
        <div>
          <h1>Shows</h1>
          <p className="dashboard__subtitle">Select a show to book seats</p>
        </div>
        <Link to="/"><Button variant="secondary">← Back</Button></Link>
      </div>

      {loading && <p className="dashboard__msg">Loading shows…</p>}
      {error && <p className="dashboard__msg dashboard__msg--error">Error: {error}</p>}

      {!loading && !error && shows.length === 0 && (
        <p className="dashboard__msg">No shows available.</p>
      )}

      <div className="dashboard__grid">
        {shows.map(show => (
          <Link key={show.id} to={`/user/show/${show.id}`} className="dashboard__link">
            <Card className="show-card">
              <h3 className="show-card__name">{show.name}</h3>
              <p className="show-card__meta">
                {new Date(show.datetime).toLocaleString()}
              </p>
              <p className="show-card__seats">
                {show.total_seats} total seats
              </p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
