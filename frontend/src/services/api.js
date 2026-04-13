const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function getShows() {
  return request('GET', '/shows');
}

export function getSeats(showId) {
  return request('GET', `/shows/${showId}/seats`);
}

export function bookSeats(showId, seatIds) {
  return request('POST', '/book', { show_id: showId, seat_ids: seatIds });
}

export function createShow(data) {
  return request('POST', '/admin/create-show', data);
}

export function deleteShow(showId) {
  return request('DELETE', `/admin/shows/${showId}`);
}
