import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { api, Profile } from '../api';

const ACTIVE_USER_STORAGE_KEY = 'biome.activeUserId';

interface UserContextType {
  activeUser: Profile | null;
  profiles: Profile[];
  loading: boolean;
  error: string | null;
  setActiveUser: (user: Profile | null) => void;
  refresh: () => Promise<void>;
  createProfile: (name: string, fitness_goal?: string) => Promise<Profile>;
  deleteProfile: (id: string) => Promise<void>;
  logout: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeUser, setActiveUserState] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const setActiveUser = useCallback((user: Profile | null) => {
    setActiveUserState(user);
    if (user) {
      localStorage.setItem(ACTIVE_USER_STORAGE_KEY, user.id);
    } else {
      localStorage.removeItem(ACTIVE_USER_STORAGE_KEY);
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.getProfiles();
      setProfiles(list);
      const storedId = localStorage.getItem(ACTIVE_USER_STORAGE_KEY);
      const restored = storedId ? list.find((p) => p.id === storedId) ?? null : null;
      setActiveUserState(restored);
      if (!restored && storedId) localStorage.removeItem(ACTIVE_USER_STORAGE_KEY);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load profiles');
      setProfiles([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const createProfile = useCallback(async (name: string, fitness_goal?: string) => {
    const created = await api.createProfile({ name, fitness_goal });
    setProfiles((prev) => [...prev, created]);
    return created;
  }, []);

  const deleteProfile = useCallback(async (id: string) => {
    await api.deleteProfile(id);
    setProfiles((prev) => prev.filter((p) => p.id !== id));
    setActiveUserState((cur) => {
      if (cur?.id === id) {
        localStorage.removeItem(ACTIVE_USER_STORAGE_KEY);
        return null;
      }
      return cur;
    });
  }, []);

  const logout = useCallback(() => {
    setActiveUser(null);
  }, [setActiveUser]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <UserContext.Provider
      value={{
        activeUser,
        profiles,
        loading,
        error,
        setActiveUser,
        refresh,
        createProfile,
        deleteProfile,
        logout,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}

export function getInitial(name: string): string {
  return name.trim().charAt(0).toUpperCase() || '?';
}
