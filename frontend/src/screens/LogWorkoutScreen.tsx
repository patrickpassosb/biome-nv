import { useState } from 'react';
import { api } from '../api';
import { Plus, X, Search } from 'lucide-react';
import { useUser } from '../contexts/UserContext';

export default function LogWorkoutScreen() {
  const { activeUser } = useUser();
  const [type, setType] = useState('Push');
  const [exercises, setExercises] = useState<{ name: string; side: string; sets: any[] }[]>([]);
  const [search, setSearch] = useState('');

  const addExercise = (name: string) => {
    setExercises(prev => [...prev, { name, side: '', sets: [{ set_number: 1, reps: '', weight_kg: '', machine_level: '', rpe: '', notes: '', is_warmup: 0 }] }]);
    setSearch('');
  };

  const addSet = (idx: number) => {
    setExercises(prev => {
      const next = [...prev];
      next[idx].sets.push({ set_number: next[idx].sets.length + 1, reps: '', weight_kg: '', machine_level: '', rpe: '', notes: '', is_warmup: 0 });
      return next;
    });
  };

  const removeExercise = (idx: number) => setExercises(prev => prev.filter((_, i) => i !== idx));

  const updateSet = (exIdx: number, setIdx: number, field: string, value: any) => {
    setExercises(prev => {
      const next = [...prev];
      next[exIdx].sets[setIdx] = { ...next[exIdx].sets[setIdx], [field]: value };
      return next;
    });
  };

  async function save() {
    if (!activeUser) return;
    const date = new Date().toISOString().split('T')[0];
    await api.logWorkout({
      date, workout_type: type + ' Day',
      exercises: exercises.map(e => ({
        exercise_name: e.name, side: e.side || null,
        sets: e.sets.map((s: any) => ({
          set_number: s.set_number,
          reps: s.reps === '' ? null : Number(s.reps),
          weight_kg: s.weight_kg === '' ? null : Number(s.weight_kg),
          machine_level: s.machine_level === '' ? null : Number(s.machine_level),
          rpe: s.rpe === '' ? null : Number(s.rpe),
          notes: s.notes || null, is_warmup: s.is_warmup
        }))
      }))
    }, activeUser.id);
    alert('Workout saved!'); setExercises([]);
  }

  const common = ['Push Up','Lat Pulldown','Squat','Leg Extension','Lateral Raises','Peck Deck','Bench Press','Bicep Curls','Dead Hang','Abs Elevation','Sit Cable Crunch','Single Leg Bulgarian Squat','Calf Raises'];
  const filtered = common.filter(e => e.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div><h1 className="text-3xl font-bold text-white">Log Workout</h1></div>
        <div className="flex flex-wrap gap-2">
          {['Push','Pull','Legs','Custom'].map(t => (
            <button key={t} onClick={() => setType(t)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${type === t ? 'bg-primary-container text-on-primary' : 'bg-surface border border-border text-on-surface-variant hover:text-white'}`}>{t}</button>
          ))}
        </div>
      </div>
      <div className="relative w-full max-w-2xl mb-8">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-on-surface-variant" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search exercises..." className="w-full h-12 bg-surface-container-low border border-border focus:border-primary-container focus:outline-none rounded-xl pl-12 pr-4 text-white" />
        {search && (
          <div className="absolute z-20 mt-2 w-full bg-surface border border-border rounded-lg max-h-60 overflow-y-auto">
            {filtered.map(e => <button key={e} onClick={() => addExercise(e)} className="w-full text-left px-4 py-3 hover:bg-surface-container-low text-white text-sm">{e}</button>)}
          </div>
        )}
      </div>
      <div className="space-y-6">
        {exercises.map((ex, exIdx) => (
          <div key={exIdx} className="bg-surface border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">{ex.name}</h3>
              <button onClick={() => removeExercise(exIdx)} className="text-on-surface-variant hover:text-red-400"><X className="w-5 h-5" /></button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-on-surface-variant text-left">
                  <th className="pb-2 text-xs uppercase">Set</th>
                  <th className="pb-2 text-xs uppercase">Reps</th>
                  <th className="pb-2 text-xs uppercase">Weight</th>
                  <th className="pb-2 text-xs uppercase">Machine</th>
                  <th className="pb-2 text-xs uppercase">RPE</th>
                  <th className="pb-2 text-xs uppercase">Notes</th>
                </tr></thead>
                <tbody>
                  {ex.sets.map((s: any, sIdx: number) => (
                    <tr key={sIdx} className="border-t border-border/50">
                      <td className="py-2 text-white font-mono">{s.set_number}</td>
                      <td className="py-2"><input type="number" value={s.reps} onChange={e => updateSet(exIdx, sIdx, 'reps', e.target.value)} className="w-16 bg-background border border-border rounded px-2 py-1 text-white text-sm" /></td>
                      <td className="py-2"><input type="number" step="0.5" value={s.weight_kg} onChange={e => updateSet(exIdx, sIdx, 'weight_kg', e.target.value)} className="w-20 bg-background border border-border rounded px-2 py-1 text-white text-sm" /></td>
                      <td className="py-2"><input type="number" value={s.machine_level} onChange={e => updateSet(exIdx, sIdx, 'machine_level', e.target.value)} className="w-16 bg-background border border-border rounded px-2 py-1 text-white text-sm" /></td>
                      <td className="py-2"><input type="number" step="0.5" value={s.rpe} onChange={e => updateSet(exIdx, sIdx, 'rpe', e.target.value)} className="w-16 bg-background border border-border rounded px-2 py-1 text-white text-sm" /></td>
                      <td className="py-2"><input value={s.notes} onChange={e => updateSet(exIdx, sIdx, 'notes', e.target.value)} placeholder="Note..." className="w-full bg-background border border-border rounded px-2 py-1 text-white text-sm" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button onClick={() => addSet(exIdx)} className="mt-4 flex items-center gap-2 text-sm text-primary-container hover:text-white transition-colors"><Plus className="w-4 h-4" /> Add set</button>
          </div>
        ))}
      </div>
      {exercises.length > 0 && (
        <button onClick={save} className="mt-8 w-full bg-primary-container text-on-primary font-semibold py-4 rounded-xl hover:opacity-90 transition-opacity">
          Save Workout
        </button>
      )}
    </div>
  );
}
