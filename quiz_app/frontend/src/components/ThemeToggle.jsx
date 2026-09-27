import { Moon, Sun } from 'lucide-react';

export default function ThemeToggle({ theme, onToggle }) {
  return <button className="theme-toggle" type="button" onClick={onToggle}
    aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
    {theme === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
  </button>;
}
