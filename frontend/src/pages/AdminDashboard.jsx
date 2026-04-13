import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getShows, createShow, deleteShow } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import StatusMessage from '../components/StatusMessage';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [shows, setShows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState({ type: null, message: null });
  const [form, setForm] = useState({ name: '', datetime: '', total_seats: 20 });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadShows();
  }, []);

  function loadShows() {
    setLoading(true);
    getShows()
      .then(setShows)
      .catch(err => setStatus({ type: 'error', message: err.message }))
      .finally(() => setLoading(false));
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.name || !form.datetime) return;
    setCreating(true);
    setStatus({ type: null, message: null });
    try {
      await createShow({
        name: form.name,
        datetime: form.datetime,
        total_seats: parseInt(form.total_seats),
      });
      setStatus({ type: 'success', message: `Show "${form.name}" created.` });
      setForm({ name: '', datetime: '', total_seats: 20 });
      loadShows();
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this show?')) return;
    try {
      await deleteShow(id);
      setStatus({ type: 'success', message: 'Show deleted.' });
      loadShows();
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    }
  }

  function handleChange(e) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  }

  return (
    <div className="admin">
      <div className="admin__header">
        <div>
          <h1>Admin</h1>
          <p className="admin__subtitle">Manage shows and seating</p>
        </div>
        <Link to="/"><Button variant="secondary">← Back</Button></Link>
      </div>

      <StatusMessage type={status.type} message={status.message} />

      {/* Create Show Form */}
      <div className="admin__section">
        <h2 className="admin__section-title">Create Show</h2>
        <form className="admin__form" onSubmit={handleCreate}>
          <div className="form-row">
            <label className="form-label">
              Show Name
              <input
                className="form-input"
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="e.g. Evening Concert"
                required
              />
            </label>
            <label className="form-label">
              Date & Time
              <input
                className="form-input"
                type="datetime-local"
                name="datetime"
                value={form.datetime}
                onChange={handleChange}
                required
              />
            </label>
          </div>
          <div className="form-row">
            <label className="form-label">
              Total Seats
              <input
                className="form-input"
                type="number"
                name="total_seats"
                value={form.total_seats}
                onChange={handleChange}
                min="1"
                max="500"
              />
            </label>
          </div>
          <Button type="submit" disabled={creating}>
            {creating ? 'Creating…' : 'Create Show'}
          </Button>
        </form>
      </div>

      {/* Show List */}
      <div className="admin__section">
        <h2 className="admin__section-title">Existing Shows</h2>
        {loading && <p className="admin__msg">Loading…</p>}
        {!loading && shows.length === 0 && <p className="admin__msg">No shows yet.</p>}
        <div className="admin__shows">
          {shows.map(show => (
            <Card key={show.id}>
              <div className="admin__show-row">
                <div>
                  <h3 className="admin__show-name">{show.name}</h3>
                  <p className="admin__show-meta">
                    {new Date(show.datetime).toLocaleString()} · {show.total_seats} seats
                  </p>
                </div>
                <Button variant="danger" onClick={() => handleDelete(show.id)}>
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
