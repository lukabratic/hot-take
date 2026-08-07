import { motion } from 'framer-motion';
import type { LeaderboardScope } from '../../types';

interface ScopeSelectorProps {
  scope: LeaderboardScope;
  onScopeChange: (scope: LeaderboardScope) => void;
}

const SCOPES: { value: LeaderboardScope; label: string }[] = [
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'alltime', label: 'All-Time' },
  { value: 'friends', label: 'Friends' },
];

/**
 * Scope selector for the leaderboard.
 * Displays tab-style buttons for switching between today, week, alltime, and friends.
 *
 * Requirements: 12.2
 */
export function ScopeSelector({ scope, onScopeChange }: ScopeSelectorProps) {
  return (
    <div
      className="flex gap-1 p-1 rounded-xl bg-gray-800/60 border border-gray-700"
      role="tablist"
      aria-label="Leaderboard scope"
    >
      {SCOPES.map(({ value, label }) => (
        <button
          key={value}
          role="tab"
          aria-selected={scope === value}
          onClick={() => onScopeChange(value)}
          className={`relative flex-1 px-3 py-2 text-sm font-medium rounded-lg
                     transition-colors duration-150
                     ${
                       scope === value
                         ? 'text-white'
                         : 'text-gray-400 hover:text-gray-300'
                     }`}
        >
          {scope === value && (
            <motion.div
              layoutId="scope-indicator"
              className="absolute inset-0 bg-gray-700 rounded-lg"
              transition={{ type: 'spring', duration: 0.3, bounce: 0.15 }}
            />
          )}
          <span className="relative z-10">{label}</span>
        </button>
      ))}
    </div>
  );
}
