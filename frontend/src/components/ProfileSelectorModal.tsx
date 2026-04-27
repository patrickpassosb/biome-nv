import { X, Check } from 'lucide-react';
import { useUser } from '../contexts/UserContext';

interface ProfileSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ProfileSelectorModal({ isOpen, onClose }: ProfileSelectorModalProps) {
  const { activeUser, setActiveUser, mockUsers } = useUser();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-surface-container-low border border-border w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-bold text-white tracking-tight">Switch Profile</h2>
          <button
            onClick={onClose}
            className="p-2 text-on-surface-variant hover:text-white hover:bg-surface-container rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4">
          <ul className="space-y-2">
            {mockUsers.map((user) => {
              const isActive = activeUser?.id === user.id;
              return (
                <li key={user.id}>
                  <button
                    onClick={() => {
                      setActiveUser(user);
                      onClose();
                    }}
                    className={`w-full flex items-center justify-between p-4 rounded-xl transition-all duration-200 ${
                      isActive
                        ? 'bg-primary-container/20 border border-primary-container/50'
                        : 'bg-surface-container hover:bg-surface-container-high border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-surface-container-high border border-border flex items-center justify-center text-primary-container font-bold text-lg">
                        {user.initial}
                      </div>
                      <div className="text-left">
                        <div className="font-sans text-base font-bold text-white">{user.name}</div>
                        <div className="text-xs text-on-surface-variant">{user.fitness_goal}</div>
                      </div>
                    </div>
                    {isActive && (
                      <div className="w-6 h-6 rounded-full bg-primary-container flex items-center justify-center">
                        <Check className="w-4 h-4 text-on-primary-container" />
                      </div>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
        
        <div className="p-4 border-t border-border bg-surface-container/50">
          <button 
            onClick={() => {
              setActiveUser(null); // Triggers logout / return to LoginScreen
              onClose();
            }}
            className="w-full py-3 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-xl transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
