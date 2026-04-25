import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { getShows, createShow, deleteShow } from '../services/api';
import './AdminDashboard.css';

/* ── Tiny inline spinner ───────────────────────────────────────── */
function Spinner({ size = 16 }) {
  return (
    <span
      className="adm-spinner"
      style={{ width: size, height: size, '--sz': `${size}px` }}
    />
  );
}

/* ── Delete confirmation modal ─────────────────────────────────── */
function DeleteModal({ show, onConfirm, onCancel, loading }) {
  const cancelRef = useRef(null);
  useEffect(() => { cancelRef.current?.focus(); }, []);

  return (
    <div className="adm-modal-backdrop" role="dialog" aria-modal="true">
      <div className="adm-modal">
        <div className="adm-modal__icon">🗑</div>
        <h2 className="adm-modal__title">Delete Show?</h2>
        <p className="adm-modal__body">
          <strong>"{show.name}"</strong> and all{' '}
          <strong>{show.total_seats} seats</strong> will be permanently removed.
          This cannot be undone.
        </p>
        <div className="adm-modal__actions">
          <button
            ref={cancelRef}
            className="adm-modal__btn adm-modal__btn--cancel"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            className="adm-modal__btn adm-modal__btn--delete"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? <><Spinner /> Deleting…</> : 'Yes, Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Toast notification ────────────────────────────────────────── */
function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(onClose, 3500);
    return () => clearTimeout(t);
  }, [toast, onClose]);

  if (!toast) return null;
  return (
    <div className={`adm-toast adm-toast--${toast.type}`}>
      <span>{toast.type === 'success' ? '✓' : '✕'}</span>
      {toast.message}
    </div>
  );
}

/* ── Main component ────────────────────────────────────────────── */
export default function AdminDashboard() {
  const [shows, setShows]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [toast, setToast]       = useState(null);
  const [form, setForm]         = useState({ name: '', datetime: '', total_seats: 30 });
  const [errors, setErrors]     = useState({});
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null); // show object to delete
  const [deleting, setDeleting] = useState(false);

  useEffect(() => { loadShows(); }, []);

  function loadShows() {
    setLoading(true);
    getShows()
      .then(setShows)
      .catch(() => showToast('error', 'Failed to load shows.'))
      .finally(() => setLoading(false));
  }

  function showToast(type, message) {
    setToast({ type, message });
  }

  /* ── Validation ──────────────────────────────────────────────── */
  function validate() {
    const e = {};
    if (!form.name.trim())    e.name = 'Show name is required.';
    if (!form.datetime)       e.datetime = 'Date & time is required.';
    if (form.total_seats < 1) e.total_seats = 'At least 1 seat required.';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  /* ── Create ──────────────────────────────────────────────────── */
  async function handleCreate(e) {
    e.preventDefault();
    if (!validate()) return;
    setCreating(true);
    try {
      await createShow({
        name: form.name.trim(),
        datetime: form.datetime,
        total_seats: parseInt(form.total_seats),
      });
      showToast('success', `"${form.name.trim()}" created with ${form.total_seats} seats.`);
      setForm({ name: '', datetime: '', total_seats: 30 });
      setErrors({});
      loadShows();
    } catch (err) {
      showToast('error', err.message);
    } finally {
      setCreating(false);
    }
  }

  /* ── Delete (two-step) ───────────────────────────────────────── */
  async function confirmDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteShow(deleteTarget.id);
      showToast('success', `"${deleteTarget.name}" deleted.`);
      loadShows();
    } catch (err) {
      showToast('error', err.message);
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  }

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: null }));
  }

  /* ── Summary stats ───────────────────────────────────────────── */
  const totalSeats = shows.reduce((acc, s) => acc + s.total_seats, 0);

  return (
    <div className="page">
      {/* ── Nav ── */}
      <header className="topnav">
        <span className="topnav__logo">🎟 <span>Ticketer</span></span>
        <div className="topnav__right">
          <span className="adm-nav-badge">⚙ Admin</span>
          <Link to="/" className="topnav__back">← Home</Link>
        </div>
      </header>

      {/* ── Toast ── */}
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* ── Delete modal ── */}
      {deleteTarget && (
        <DeleteModal
          show={deleteTarget}
          onConfirm={confirmDelete}
          onCancel={() => setDeleteTarget(null)}
          loading={deleting}
        />
      )}

      <main className="adm-main">

        {/* ── Page heading ── */}
        <div className="adm-heading">
          <div>
            <h1 className="adm-heading__title">Admin Dashboard</h1>
            <p className="adm-heading__sub">Create and manage shows and seating capacities.</p>
          </div>
        </div>

        {/* ── Summary stats ── */}
        {!loading && (
          <div className="adm-summary">
            <div className="adm-summary__stat">
              <span className="adm-summary__val">{shows.length}</span>
              <span className="adm-summary__lbl">Shows</span>
            </div>
            <div className="adm-summary__divider" />
            <div className="adm-summary__stat">
              <span className="adm-summary__val">{totalSeats}</span>
              <span className="adm-summary__lbl">Total Seats</span>
            </div>
            <div className="adm-summary__divider" />
            <div className="adm-summary__stat">
              <span className="adm-summary__val adm-summary__val--accent">
                {shows.length > 0
                  ? Math.round(totalSeats / shows.length)
                  : '—'}
              </span>
              <span className="adm-summary__lbl">Avg Capacity</span>
            </div>
          </div>
        )}

        {/* ── Create Show Form ── */}
        <section className="adm-section">
          <div className="adm-section__title-row">
            <h2 className="adm-section__title">Create New Show</h2>
          </div>

          <form className="adm-form" onSubmit={handleCreate} noValidate>
            {/* Row 1: name + datetime */}
            <div className="adm-form__row">
              <div className="adm-field">
                <label className="adm-label" htmlFor="name">Show Name</label>
                <input
                  className={`adm-input${errors.name ? ' adm-input--error' : ''}`}
                  id="name"
                  type="text"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  placeholder="e.g. Evening Concert"
                  autoComplete="off"
                />
                {errors.name && <span className="adm-field-error">{errors.name}</span>}
              </div>

              <div className="adm-field">
                <label className="adm-label" htmlFor="datetime">Date &amp; Time</label>
                <input
                  className={`adm-input${errors.datetime ? ' adm-input--error' : ''}`}
                  id="datetime"
                  type="datetime-local"
                  name="datetime"
                  value={form.datetime}
                  onChange={handleChange}
                />
                {errors.datetime && <span className="adm-field-error">{errors.datetime}</span>}
              </div>
            </div>

            {/* Row 2: seat slider */}
            <div className="adm-field">
              <div className="adm-label-row">
                <label className="adm-label" htmlFor="total_seats">Total Seats</label>
                <span className="adm-seat-count">{form.total_seats} seats</span>
              </div>
              <input
                className="adm-slider"
                id="total_seats"
                type="range"
                name="total_seats"
                value={form.total_seats}
                onChange={handleChange}
                min="10"
                max="300"
                step="10"
              />
              <div className="adm-slider-ticks">
                <span>10</span><span>100</span><span>200</span><span>300</span>
              </div>
            </div>

            {/* Submit */}
            <div className="adm-form__footer">
              <button className="adm-create-btn" type="submit" disabled={creating}>
                {creating ? <><Spinner /> Creating…</> : '＋ Create Show'}
              </button>
            </div>
          </form>
        </section>

        {/* ── Show List ── */}
        <section className="adm-section">
          <div className="adm-section__header">
            <h2 className="adm-section__title">Existing Shows</h2>
            {!loading && shows.length > 0 && (
              <span className="adm-badge">{shows.length} total</span>
            )}
          </div>

          {loading && (
            <div className="adm-center-loading">
              <Spinner size={24} />
              <span>Loading shows…</span>
            </div>
          )}

          {!loading && shows.length === 0 && (
            <div className="adm-empty">
              <span className="adm-empty__icon">🎪</span>
              <p>No shows yet. Create your first one above.</p>
            </div>
          )}

          {!loading && shows.length > 0 && (
            <div className="adm-shows">
              {shows.map(show => {
                const date = new Date(show.datetime);
                const isPast = date < new Date();
                return (
                  <div key={show.id} className={`adm-show-card${isPast ? ' adm-show-card--past' : ''}`}>
                    <div className="adm-show-card__icon">🎭</div>

                    <div className="adm-show-card__body">
                      <div className="adm-show-card__top">
                        <h3 className="adm-show-card__name">{show.name}</h3>
                        {isPast && <span className="adm-show-card__past-tag">Past</span>}
                      </div>
                      <div className="adm-show-card__meta">
                        <span>📅 {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                        <span>⏰ {date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                        <span>💺 {show.total_seats} seats</span>
                        <span className="adm-show-card__id">ID #{show.id}</span>
                      </div>
                    </div>

                    <button
                      className="adm-delete-btn"
                      onClick={() => setDeleteTarget(show)}
                      aria-label={`Delete ${show.name}`}
                      title="Delete show"
                    >
                      🗑
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
