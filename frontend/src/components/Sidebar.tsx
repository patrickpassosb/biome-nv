import { NavLink, useLocation } from 'react-router-dom';
import { Calendar, TrendingUp, Dumbbell, MessageCircle, Bot } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Today', icon: Calendar },
  { path: '/progress', label: 'Progress', icon: TrendingUp },
  { path: '/log', label: 'Log Workout', icon: Dumbbell },
  { path: '/ask', label: 'Ask Coach', icon: MessageCircle },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <nav className="hidden md:flex w-[240px] h-screen border-r border-border bg-background fixed left-0 top-0 flex-col justify-between py-8 z-40">
      <div>
        <div className="px-6 mb-8 flex items-center gap-2">
          <Bot className="w-6 h-6 text-primary-container" />
          <span className="text-xl font-bold tracking-tighter text-white">Biome</span>
        </div>
        <div className="px-6 mb-8 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-surface-container-high border border-border flex items-center justify-center text-primary-container font-bold text-sm">
            P
          </div>
          <div>
            <div className="font-sans text-sm tracking-tight font-medium text-white">Patrick</div>
            <div className="text-[10px] text-on-surface-variant">Building muscle · Week 12</div>
          </div>
        </div>
        <ul className="flex flex-col gap-1 w-full">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={`flex items-center gap-3 w-full pl-4 py-2 transition-all duration-200 ${
                    isActive
                      ? 'text-white border-l-2 border-primary-container bg-surface-container-low opacity-90'
                      : 'text-on-surface-variant hover:text-white hover:bg-surface-container-low/50 border-l-2 border-transparent'
                  }`}
                >
                  <item.icon className="w-[18px] h-[18px]" />
                  <span className="font-sans text-sm tracking-tight font-medium">{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
