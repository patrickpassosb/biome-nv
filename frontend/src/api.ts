const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson(path: string, opts?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  importCsv: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return fetchJson('/import', { method: 'POST', body: form });
  },
  getWorkouts: () => fetchJson('/workouts'),
  getRecommend: (type: string) => fetchJson(`/recommend?workout_type=${encodeURIComponent(type)}`),
  getExerciseMetrics: () => fetchJson('/metrics/exercises'),
  getVolumeMetrics: () => fetchJson('/metrics/volume'),
  getAsymmetryMetrics: () => fetchJson('/metrics/asymmetry'),
  logWorkout: (body: unknown) => fetchJson('/workouts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }),
  chat: (message: string, history: { role: string; content: string }[]) =>
    fetchJson('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history })
    }),
};
