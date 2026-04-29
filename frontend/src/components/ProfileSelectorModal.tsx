import { useState } from 'react';
import { Check, Loader2, Plus, UserPlus, X } from 'lucide-react';
import { useUser, getInitial } from '../contexts/UserContext';

interface ProfileSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ProfileSelectorModal({ isOpen, onClose }: ProfileSelectorModalProps) {
  const { activeUser, profiles, setActiveUser, createProfile, logout } = useUser();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleClose = () => {
    setShowCreate(false);
    setName('');
    setGoal('');
    setError(null);
    onClose();
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const created = await createProfile(name.trim(), goal.trim() || undefined);
      setActiveUser(created);
      handleClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create profile');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-surface-container-low border border-border w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-bold text-white tracking-tight">
            {showCreate ? 'New profile' : 'Switch profile'}
          </h2>
          <button
            onClick={handleClose}
            className="p-2 text-on-surface-variant hover:text-white hover:bg-surface-container rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {!showCreate ? (
          <>
            <div className="p-4">
              <ul className="space-y-2">
                {profiles.map((profile) => {
                  const isActive = activeUser?.id === profile.id;
                  return (
                    <li key={profile.id}>
                      <button
                        onClick={() => {
                          setActiveUser(profile);
                          handleClose();
                        }}
                        className={`w-full flex items-center justify-between p-4 rounded-xl transition-all duration-200 ${
                          isActive
                            ? 'bg-primary-container/20 border border-primary-container/50'
                            : 'bg-surface-container hover:bg-surface-container-high border border-transparent'
                        }`}
                      >
                        <div className="flex items-center gap-4 min-w-0">
                          <div className="w-12 h-12 shrink-0 rounded-full bg-surface-container-high border border-border flex items-center justify-center text-primary-container font-bold text-lg">
                            {getInitial(profile.name)}
                          </div>
                          <div className="text-left min-w-0">
                            <div className="font-sans text-base font-bold text-white">{profile.name}</div>
                            {profile.fitness_goal && (
                              <div className="text-xs text-on-surface-variant truncate">{profile.fitness_goal}</div>
                            )}
                          </div>
                        </div>
                        {isActive && (
                          <div className="w-6 h-6 shrink-0 rounded-full bg-primary-container flex items-center justify-center ml-2">
                            <Check className="w-4 h-4 text-on-primary-container" />
                          </div>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>

              <button
                onClick={() => setShowCreate(true)}
                className="mt-3 w-full flex items-center justify-center gap-2 py-3 text-sm font-medium text-primary-container hover:bg-primary-container/10 rounded-xl border border-dashed border-primary-container/40 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Create new profile</span>
              </button>
            </div>

            <div className="p-4 border-t border-border bg-surface-container/50">
              <button
                onClick={() => {
                  logout();
                  handleClose();
                }}
                className="w-full py-3 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-xl transition-colors"
              >
                Sign out
              </button>
            </div>
          </>
        ) : (
          <form onSubmit={handleCreate} className="p-4 space-y-4">
            <div>
              <label htmlFor="profile-name-modal" className="block text-sm font-medium text-on-surface-variant mb-2">
                Name
              </label>
              <input
                id="profile-name-modal"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Jim"
                required
                autoFocus
                className="w-full bg-surface-container border border-border rounded-xl px-4 py-3 text-white placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-container"
              />
            </div>
            <div>
              <label htmlFor="profile-goal-modal" className="block text-sm font-medium text-on-surface-variant mb-2">
                Fitness goal <span className="text-on-surface-variant/50">(optional)</span>
              </label>
              <input
                id="profile-goal-modal"
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Cutting fat"
                className="w-full bg-surface-container border border-border rounded-xl px-4 py-3 text-white placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-container"
              />
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="flex-1 py-3 text-sm font-medium text-on-surface-variant hover:text-white border border-border rounded-xl"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={submitting || !name.trim()}
                className="flex-1 bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                <span>Create</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
