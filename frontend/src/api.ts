const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson(path: string, opts?: RequestInit, userId?: string) {
  const headers = new Headers(opts?.headers);
  if (userId) {
    headers.set('X-User-ID', userId);
  }
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  importCsv: (file: File, userId?: string) => {
    const form = new FormData();
    form.append('file', file);
    return fetchJson('/import', { method: 'POST', body: form }, userId);
  },
  getWorkouts: (userId?: string) => fetchJson('/workouts', undefined, userId),
  getRecommend: (type: string, userId?: string) => fetchJson(`/recommend?workout_type=${encodeURIComponent(type)}`, undefined, userId),
  getExerciseMetrics: (userId?: string) => fetchJson('/metrics/exercises', undefined, userId),
  getVolumeMetrics: (userId?: string) => fetchJson('/metrics/volume', undefined, userId),
  getAsymmetryMetrics: (userId?: string) => fetchJson('/metrics/asymmetry', undefined, userId),
  logWorkout: (body: unknown, userId?: string) => fetchJson('/workouts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }, userId),
  chat: (message: string, userId?: string) =>
    fetchJson('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    }, userId),
};
