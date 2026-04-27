import { useState, useEffect } from 'react';
import { api } from '../api';
import { Loader2, Play } from 'lucide-react';
import { useUser } from '../contexts/UserContext';

interface Exercise {
  name: string;
  order: number;
  sets: number;
  target_reps: string;
  target_weight_kg: number | null;
  target_machine_level: number | null;
  target_rpe: string;
  rest_seconds: number;
  rationale: string;
}

interface Recommendation {
  session_plan: {
    workout_type: string;
    estimated_duration_minutes: number;
    exercises: Exercise[];
  };
  overall_reasoning: string;
  warnings: string[];
  confidence: string;
}

export default function TodayScreen() {
  const { activeUser } = useUser();
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  useEffect(() => {
    if (!activeUser) return;
    setLoading(true);
    api.getRecommend('Push Day', activeUser.id)
      .then((data) => { setRec(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [activeUser]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-container" />
      </div>
    );
  }

  const plan = rec?.session_plan;
  const confidenceWidth = rec?.confidence === 'high' ? '100%' : rec?.confidence === 'medium' ? '60%' : '30%';

  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Today</h1>
          <div className="text-on-surface-variant">{today} · {plan?.workout_type || 'Push Day'}</div>
        </div>
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-border">
          <span className="text-on-surface-variant text-xs uppercase tracking-wider">Estimated {plan?.estimated_duration_minutes || 55} min</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 flex flex-col gap-6">
          {plan?.exercises.map((ex) => (
            <div key={ex.order} className="bg-surface border border-border rounded-xl p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-1">{ex.name}</h3>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-background border border-border rounded-lg p-4">
                  <div className="text-[11px] uppercase tracking-wider text-on-surface-variant mb-1">Sets x Reps</div>
                  <div className="text-2xl font-mono font-medium text-white">{ex.sets} x {ex.target_reps}</div>
                </div>
                <div className="bg-background border border-border rounded-lg p-4">
                  <div className="text-[11px] uppercase tracking-wider text-on-surface-variant mb-1">Weight</div>
                  <div className="text-2xl font-mono font-medium text-white">
                    {ex.target_weight_kg ?? ex.target_machine_level ?? '-'}<span className="text-sm text-on-surface-variant ml-1">{ex.target_machine_level ? 'lvl' : 'kg'}</span>
                  </div>
                </div>
                <div className="bg-background border border-border rounded-lg p-4">
                  <div className="text-[11px] uppercase tracking-wider text-on-surface-variant mb-1">Target RPE</div>
                  <div className="text-2xl font-mono font-medium text-primary-container">{ex.target_rpe}</div>
                </div>
              </div>
              <div className="text-on-surface-variant text-sm border-l-2 border-border pl-3">{ex.rationale}</div>
            </div>
          ))}
          <button className="w-full bg-primary-container text-on-primary font-semibold py-4 rounded-xl hover:opacity-90 transition-opacity flex items-center justify-center gap-2">
            <Play className="w-5 h-5" /> Start Workout
          </button>
        </div>

        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-surface border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-3">Today's Focus</h3>
            <p className="text-sm text-on-surface-variant">{rec?.overall_reasoning || 'Volume accumulation with controlled RPE.'}</p>
          </div>

          {(rec?.warnings?.length ?? 0) > 0 && (
            <div className="bg-surface border border-primary-container/30 rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-primary-container/50" />
              <h3 className="text-lg font-semibold text-white mb-2">Warnings</h3>
              {rec?.warnings.map((w, i) => (
                <p key={i} className="text-sm text-on-surface-variant">{w}</p>
              ))}
            </div>
          )}

          <div className="bg-surface border border-border rounded-xl p-6">
            <div className="flex justify-between items-end mb-2">
              <span className="text-[11px] uppercase tracking-wider text-on-surface-variant">AI Confidence</span>
              <span className="text-lg font-mono text-white">{rec?.confidence === 'high' ? '88%' : rec?.confidence === 'medium' ? '65%' : '40%'}</span>
            </div>
            <div className="w-full bg-background rounded-full h-1.5 border border-border">
              <div className="bg-primary-container h-1.5 rounded-full transition-all duration-500" style={{ width: confidenceWidth }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
