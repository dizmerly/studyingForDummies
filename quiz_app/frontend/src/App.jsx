import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { History, HelpCircle, X, LogOut, Settings } from 'lucide-react';
import AuthScreen from './components/AuthScreen';
import StartScreen from './components/StartScreen';
import LandingScreen from './components/LandingScreen';
import QuizScreen from './components/QuizScreen';
import ResultsScreen from './components/ResultsScreen';
import HistoryScreen from './components/HistoryScreen';
import SettingsScreen from './components/SettingsScreen';
import ThemeToggle from './components/ThemeToggle';
import { api } from './services/api';

function App() {
  const [screen, setScreen] = useState('landing'); // landing, start, quiz, results, history, auth
  const [showHelp, setShowHelp] = useState(false);
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const data = await api.checkAuth();
        if (data.authenticated) {
          setUser(data.user);
        }
      } catch (err) {
        console.error('Auth check failed:', err);
      } finally {
        setAuthChecked(true);
      }
    };
    checkAuth();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setScreen('landing');
  };

  const handleLogout = async () => {
    try {
      await api.logout();
      setUser(null);
      setScreen('landing');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const handleQuizStart = () => {
    setScreen('quiz');
  };

  const handleQuizComplete = () => {
    setScreen('results');
  };

  const handleRestart = async () => {
    try {
      await api.restartQuiz();
      setScreen('quiz');
    } catch (err) {
      console.error(err);
    }
  };

  const handleNewQuiz = async () => {
    try {
      await api.resetQuiz();
      setScreen('start');
    } catch (err) {
      console.error(err);
    }
  };

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-secondary">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-text transition-colors duration-300">
      <div className="container relative">
        {/* Header */}
        <header className="flex justify-between items-center">
          <button
            onClick={() => setScreen('landing')}
            className="logo-btn font-bold text-2xl"
          >
            StudyingFor<span className="gradient-text">Dummies</span>
          </button>
          <div className="flex items-center gap-3">
            {user && (
              <>
                <button
                  onClick={() => setScreen('settings')}
                  className="icon-btn"
                  title="Settings"
                >
                  <Settings className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setScreen('history')}
                  className="icon-btn"
                  title="History"
                >
                  <History className="w-5 h-5" />
                </button>
                <div className="text-sm text-secondary hidden sm:block">
                  {user.email}
                </div>
                <button
                  onClick={handleLogout}
                  className="icon-btn"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </>
            )}
            {!user && (
              <button
                onClick={() => setScreen('auth')}
                className="btn btn-primary"
              >
                Sign In
              </button>
            )}
            <button
              onClick={() => setShowHelp(true)}
              className="icon-btn"
              title="Help"
            >
              <HelpCircle className="w-5 h-5" />
            </button>
            <ThemeToggle />
          </div>
        </header>

        {/* Main Content */}
        <main>
          <AnimatePresence mode="wait">
            {screen === 'auth' && (
              <AuthScreen key="auth" onLogin={handleLogin} />
            )}
            {screen === 'landing' && (
              <LandingScreen
                key="landing"
                onStart={() => user ? setScreen('start') : setScreen('auth')}
                onHistory={() => user ? setScreen('history') : setScreen('auth')}
              />
            )}
            {screen === 'start' && (
              <StartScreen key="start" onQuizStart={handleQuizStart} />
            )}
            {screen === 'quiz' && (
              <QuizScreen key="quiz" onComplete={handleQuizComplete} />
            )}
            {screen === 'results' && (
              <ResultsScreen key="results" onRestart={handleRestart} onHome={handleNewQuiz} />
            )}
            {screen === 'history' && (
              <HistoryScreen key="history" onBack={() => setScreen('landing')} />
            )}
            {screen === 'settings' && (
              <SettingsScreen key="settings" onBack={() => setScreen('landing')} />
            )}
          </AnimatePresence>
        </main>

        {/* Help Modal */}
        <AnimatePresence>
          {showHelp && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm"
              onClick={() => setShowHelp(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="card max-w-md w-full relative"
                onClick={e => e.stopPropagation()}
              >
                <button
                  onClick={() => setShowHelp(false)}
                  className="absolute top-4 right-4 p-1 hover:bg-background rounded-full"
                >
                  <X className="w-5 h-5" />
                </button>

                <h2 className="text-xl font-bold mb-4">How to Use</h2>
                <div className="space-y-4 text-secondary text-sm overflow-y-auto max-h-[60vh] pr-2">
                  <p><strong>Format Instructions:</strong></p>
                  <p>Your input file must strictly follow this format:</p>
                  <div className="bg-background p-3 rounded-md font-mono text-xs border border-border whitespace-pre-wrap">
                    {`"""QUESTION"""
The question text goes here.

For code questions, wrap code in """CODE""" blocks:
"""CODE"""
your code here
"""CODE"""

"""CHOICES"""
A: ...
B: ...
C: ...
D: ...
"""ANSWER"""
A-D (single capital letter only)`}
                  </div>

                  <p><strong>Example with Code:</strong></p>
                  <div className="bg-background p-3 rounded-md font-mono text-xs border border-border whitespace-pre-wrap">
                    {`"""QUESTION"""
What does this code print?
"""CODE"""
int main() {
    int x = 5;
    cout << x * 2;
    return 0;
}
"""CODE"""
"""CHOICES"""
A: 5
B: 10
C: 25
D: 0
"""ANSWER"""
B`}
                  </div>
                  <p>
                    <strong>Shortcuts:</strong>
                    <br />• 1-4 or A-D: Select answer
                    <br />• Enter/Space: Submit answer
                  </p>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;
