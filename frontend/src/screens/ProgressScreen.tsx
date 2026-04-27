import { useState, useEffect } from 'react';
import { api } from '../api';
import { Loader2, Search } from 'lucide-react';
import { useUser } from '../contexts/UserContext';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  BarChart, Bar
} from 'recharts';

interface ExerciseMetric {
  exercise: string;
  canonical: string;
  side: string;
  sessions: number;
  current_load: number;
  max_load: number;
  avg_rpe: number;
  trend: string;
  status: string;
}

interface Asymmetry {
  exercise: string;
  rs_reps: number;
  ls_reps: number;
  rs_rpe: number;
  ls_rpe: number;
  rep_gap_pct: number;
  rpe_gap: number;
  flagged: boolean;
}

export default function ProgressScreen() {
  const { activeUser } = useUser();
  const [tab, setTab] = useState<'exercises' | 'volume' | 'asymmetries'>('exercises');
  const [exercises, setExercises] = useState<ExerciseMetric[]>([]);
  const [volume, setVolume] = useState<any[]>([]);
  const [asymmetry, setAsymmetry] = useState<Asymmetry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEx, setSelectedEx] = useState<string>('');
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (!activeUser) return;
    setLoading(true);
    Promise.all([
      api.getExerciseMetrics(activeUser.id),
      api.getVolumeMetrics(activeUser.id),
      api.getAsymmetryMetrics(activeUser.id)
    ]).then(([e, v, a]) => {
      setExercises(e);
      setVolume(v);
      setAsymmetry(a);
      if (e.length > 0) setSelectedEx(e[0].exercise);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [activeUser]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-container" />
      </div>
    );
  }

  const filtered = exercises.filter(e => e.exercise.toLowerCase().includes(filter.toLowerCase()));

  const statusColor = (status: string) => {
    if (status === 'progressing') return 'text-green-400 bg-green-400/10 border-green-400/20';
    if (status === 'stalled') return 'text-red-400 bg-red-400/10 border-red-400/20';
    return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
  };

  return (
    <div>
      <div className="flex items-end justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Progress</h1>
          <p className="text-on-surface-variant mt-1">Last 8 weeks</p>
        </div>
      </div>

      <div className="flex gap-6 border-b border-border mb-6">
        {(['exercises', 'volume', 'asymmetries'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-3 text-lg font-medium capitalize transition-colors ${
              tab === t ? 'text-primary-container border-b-2 border-primary-container' : 'text-on-surface-variant hover:text-white'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'exercises' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 flex flex-col gap-2">
            <div className="relative mb-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                value={filter}
                onChange={e => setFilter(e.target.value)}
                placeholder="Filter exercises..."
                className="w-full h-10 bg-surface-container-low border border-border rounded-lg pl-10 pr-4 text-sm text-white placeholder:text-on-surface-variant focus:border-primary-container focus:outline-none"
              />
            </div>
            {filtered.map((ex) => (
              <button
                key={ex.exercise}
                onClick={() => setSelectedEx(ex.exercise)}
                className={`flex items-center justify-between p-4 rounded-lg border transition-colors text-left ${
                  selectedEx === ex.exercise
                    ? 'bg-surface-container border-l-2 border-l-primary-container border-y border-r border-border'
                    : 'bg-surface border-border hover:bg-surface-container-low'
                }`}
              >
                <div>
                  <div className="text-white font-medium">{ex.exercise}</div>
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[11px] uppercase tracking-wider border ${statusColor(ex.status)}`}>
                    {ex.status}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-xl font-mono text-white">{ex.current_load || ex.max_load || '-'}</div>
                </div>
              </button>
            ))}
          </div>

          <div className="lg:col-span-7">
            <div className="bg-surface border border-border rounded-xl p-6 min-h-[400px]">
              <h2 className="text-xl font-semibold text-white mb-2">{selectedEx}</h2>
              <p className="text-sm text-on-surface-variant mb-6">Load trend over time</p>
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={exercises.filter(e => e.exercise === selectedEx).map(e => ({ week: 'W1', load: e.current_load || e.max_load }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                    <XAxis dataKey="week" stroke="#737373" />
                    <YAxis stroke="#737373" />
                    <Tooltip contentStyle={{ backgroundColor: '#141414', border: '1px solid #262626', color: '#f0e0d1' }} />
                    <Line type="monotone" dataKey="load" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === 'volume' && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Weekly Volume by Muscle Group</h2>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={volume}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="week" stroke="#737373" />
                <YAxis stroke="#737373" />
                <Tooltip contentStyle={{ backgroundColor: '#141414', border: '1px solid #262626', color: '#f0e0d1' }} />
                <Bar dataKey="muscles.chest" fill="#f59e0b" name="Chest" />
                <Bar dataKey="muscles.back" fill="#3b82f6" name="Back" />
                <Bar dataKey="muscles.legs" fill="#10b981" name="Legs" />
                <Bar dataKey="muscles.shoulders" fill="#8b5cf6" name="Shoulders" />
                <Bar dataKey="muscles.arms" fill="#ef4444" name="Arms" />
                <Bar dataKey="muscles.abs" fill="#06b6d4" name="Core" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {volume.length >= 2 && (
            <div className="mt-4 flex items-center gap-2 text-sm">
              <span className="text-on-surface-variant">This week:</span>
              <span className="text-white font-mono">{(Object.values(volume[volume.length - 1].muscles) as number[]).reduce((a, b) => a + b, 0).toFixed(0)}</span>
              <span className="text-on-surface-variant">sets · Last week:</span>
              <span className="text-white font-mono">{(Object.values(volume[volume.length - 2].muscles) as number[]).reduce((a, b) => a + b, 0).toFixed(0)}</span>
            </div>
          )}
        </div>
      )}

      {tab === 'asymmetries' && (
        <div className="space-y-4">
          {asymmetry.length === 0 ? (
            <div className="text-on-surface-variant text-center py-12">No asymmetries detected in the last 4 weeks.</div>
          ) : (
            asymmetry.map(a => (
              <div key={a.exercise} className={`bg-surface border rounded-xl p-6 ${a.flagged ? 'border-red-400/30' : 'border-border'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-white">{a.exercise}</h3>
                  {a.flagged && <span className="px-2 py-0.5 rounded text-xs bg-red-400/10 text-red-400 border border-red-400/20">Flagged</span>}
                </div>
                <div className="grid grid-cols-2 gap-4 mb-2">
                  <div>
                    <div className="text-xs text-on-surface-variant uppercase tracking-wider mb-1">Right Side</div>
                    <div className="text-lg font-mono text-white">{a.rs_reps} reps · RPE {a.rs_rpe}</div>
                  </div>
                  <div>
                    <div className="text-xs text-on-surface-variant uppercase tracking-wider mb-1">Left Side</div>
                    <div className="text-lg font-mono text-white">{a.ls_reps} reps · RPE {a.ls_rpe}</div>
                  </div>
                </div>
                <div className="w-full bg-background rounded-full h-2 border border-border">
                  <div
                    className={`h-2 rounded-full transition-all ${a.flagged ? 'bg-red-400' : 'bg-primary-container'}`}
                    style={{ width: `${Math.min(a.rep_gap_pct, 100)}%` }}
                  />
                </div>
                <p className="text-sm text-on-surface-variant mt-2">
                  Rep gap: {a.rep_gap_pct}% · RPE gap: {a.rpe_gap}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
