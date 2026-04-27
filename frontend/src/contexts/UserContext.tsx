import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface User {
  id: string;
  name: string;
  initial: string;
  fitness_goal: string;
}

interface UserContextType {
  activeUser: User | null;
  setActiveUser: (user: User | null) => void;
  mockUsers: User[];
  logout: () => void;
}

export const mockUsers: User[] = [
  {
    id: 'user_001',
    name: 'Patrick',
    initial: 'P',
    fitness_goal: 'Building muscle · Week 12',
  },
  {
    id: 'user_002',
    name: 'Jim',
    initial: 'J',
    fitness_goal: 'Cutting fat · Week 4',
  },
  {
    id: 'user_003',
    name: 'Sarah',
    initial: 'S',
    fitness_goal: 'Endurance training · Week 8',
  },
];

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [activeUser, setActiveUser] = useState<User | null>(null);

  const logout = () => {
    setActiveUser(null);
  };

  return (
    <UserContext.Provider value={{ activeUser, setActiveUser, mockUsers, logout }}>
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
