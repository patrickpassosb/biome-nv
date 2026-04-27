import { useState } from 'react';
import { useUser, mockUsers } from '../contexts/UserContext';
import { Bot, LogIn } from 'lucide-react';

export default function LoginScreen() {
  const { setActiveUser } = useUser();
  const [selectedUserId, setSelectedUserId] = useState(mockUsers[0].id);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    const user = mockUsers.find((u) => u.id === selectedUserId);
    if (user) {
      setActiveUser(user);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="w-full max-w-md bg-surface-container-low border border-border rounded-2xl p-8 shadow-xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-primary-container rounded-full flex items-center justify-center mb-4">
            <Bot className="w-8 h-8 text-on-primary-container" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Welcome to Biome</h1>
          <p className="text-on-surface-variant text-sm mt-2 text-center">
            Sign in to access your personal AI strength coach and track your progress.
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label htmlFor="user-select" className="block text-sm font-medium text-on-surface-variant mb-2">
              Select Profile (Mock Login)
            </label>
            <select
              id="user-select"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="w-full bg-surface-container border border-border rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors appearance-none"
            >
              {mockUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name} - {user.fitness_goal}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            className="w-full bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors"
          >
            <LogIn className="w-5 h-5" />
            <span>Sign In</span>
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-border text-center">
          <p className="text-xs text-on-surface-variant">
            This is a mock authentication screen for local development. In production, this will be replaced by Supabase Auth.
          </p>
        </div>
      </div>
    </div>
  );
}
