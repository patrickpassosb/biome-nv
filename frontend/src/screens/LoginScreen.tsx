import { useState } from 'react';
import { useUser, getInitial } from '../contexts/UserContext';
import { Bot, Loader2, Plus, UserPlus } from 'lucide-react';

export default function LoginScreen() {
  const { profiles, loading, error, setActiveUser, createProfile, refresh } = useUser();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const created = await createProfile(name.trim(), goal.trim() || undefined);
      setActiveUser(created);
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to create profile');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary-container" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-6">
        <div className="w-full max-w-md bg-surface-container-low border border-border rounded-2xl p-8 text-center">
          <h1 className="text-xl font-bold text-white mb-2">Cannot reach the server</h1>
          <p className="text-sm text-on-surface-variant mb-6 break-words">{error}</p>
          <button
            onClick={refresh}
            className="bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-medium py-2 px-4 rounded-xl"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const empty = profiles.length === 0;
  const showForm = empty || showCreate;

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="w-full max-w-md bg-surface-container-low border border-border rounded-2xl p-8 shadow-xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-primary-container rounded-full flex items-center justify-center mb-4">
            <Bot className="w-8 h-8 text-on-primary-container" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Welcome to Biome</h1>
          <p className="text-on-surface-variant text-sm mt-2 text-center">
            {empty ? 'Create your profile to get started.' : 'Choose a profile to continue.'}
          </p>
        </div>

        {!showForm && (
          <ul className="space-y-2 mb-4">
            {profiles.map((profile) => (
              <li key={profile.id}>
                <button
                  onClick={() => setActiveUser(profile)}
                  className="w-full flex items-center gap-4 p-4 rounded-xl bg-surface-container hover:bg-surface-container-high border border-transparent transition-colors"
                >
                  <div className="w-12 h-12 rounded-full bg-surface-container-high border border-border flex items-center justify-center text-primary-container font-bold text-lg">
                    {getInitial(profile.name)}
                  </div>
                  <div className="text-left flex-1 min-w-0">
                    <div className="font-sans text-base font-bold text-white">{profile.name}</div>
                    {profile.fitness_goal && (
                      <div className="text-xs text-on-surface-variant truncate">{profile.fitness_goal}</div>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}

        {!showForm ? (
          <button
            onClick={() => setShowCreate(true)}
            className="w-full flex items-center justify-center gap-2 py-3 text-sm font-medium text-primary-container hover:bg-primary-container/10 rounded-xl border border-dashed border-primary-container/40 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Create new profile</span>
          </button>
        ) : (
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label htmlFor="profile-name" className="block text-sm font-medium text-on-surface-variant mb-2">
                Name
              </label>
              <input
                id="profile-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Patrick"
                required
                autoFocus
                className="w-full bg-surface-container border border-border rounded-xl px-4 py-3 text-white placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-container"
              />
            </div>
            <div>
              <label htmlFor="profile-goal" className="block text-sm font-medium text-on-surface-variant mb-2">
                Fitness goal <span className="text-on-surface-variant/50">(optional)</span>
              </label>
              <input
                id="profile-goal"
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Building muscle"
                className="w-full bg-surface-container border border-border rounded-xl px-4 py-3 text-white placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-container"
              />
            </div>

            {submitError && <p className="text-sm text-red-400">{submitError}</p>}

            <div className="flex gap-2">
              {!empty && (
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 py-3 text-sm font-medium text-on-surface-variant hover:text-white border border-border rounded-xl"
                >
                  Back
                </button>
              )}
              <button
                type="submit"
                disabled={submitting || !name.trim()}
                className="flex-1 bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                <span>Create profile</span>
              </button>
            </div>
          </form>
        )}

        <div className="mt-8 pt-6 border-t border-border text-center">
          <p className="text-xs text-on-surface-variant">
            Profiles are stored locally on your device.
          </p>
        </div>
      </div>
    </div>
  );
}
