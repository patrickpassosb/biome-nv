import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TodayScreen from './screens/TodayScreen';
import ProgressScreen from './screens/ProgressScreen';
import LogWorkoutScreen from './screens/LogWorkoutScreen';
import AskCoachScreen from './screens/AskCoachScreen';
import LoginScreen from './screens/LoginScreen';
import { useUser } from './contexts/UserContext';

function App() {
  const { activeUser } = useUser();

  if (!activeUser) {
    return <LoginScreen />;
  }

  return (
    <div className="flex min-h-screen bg-background text-on-surface">
      <Sidebar />
      <main className="flex-1 md:ml-[240px] min-h-screen">
        <div className="max-w-[1200px] mx-auto w-full px-6 py-8 md:py-12">
          <Routes>
            <Route path="/" element={<TodayScreen />} />
            <Route path="/progress" element={<ProgressScreen />} />
            <Route path="/log" element={<LogWorkoutScreen />} />
            <Route path="/ask" element={<AskCoachScreen />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default App;
