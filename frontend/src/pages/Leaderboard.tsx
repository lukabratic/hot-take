import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useLeaderboard } from '../hooks/useLeaderboard';
import { LeaderboardTable } from '../components/leaderboard/LeaderboardTable';
import { ScopeSelector } from '../components/leaderboard/ScopeSelector';
import { CategoryLeaderboard } from '../components/leaderboard/CategoryLeaderboard';

type LeaderboardView = 'overall' | 'category';

/**
 * Leaderboard page at route `/leaderboard`.
 * Displays ranked users by score with scope switching.
 * Supports toggling between Overall and By Category views.
 *
 * Requirements: 6.2, 12.1, 12.2, 12.5
 */
export function Leaderboard() {
  const [view, setView] = useState<LeaderboardView>('overall');
  const { entries, loading, error, scope, setScope } = useLeaderboard('today');

  return (
    <div className="min-h-screen flex flex-col items-center p-4 pt-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-lg space-y-6"
      >
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Leaderboard</h1>
            <p className="text-sm text-gray-400">See who&apos;s got the hottest takes</p>
          </div>
          <Link
            to="/"
            className="text-sm text-nba-gold hover:underline"
            aria-label="Back to home"
          >
            ← Home
          </Link>
        </header>

        {/* View Toggle: Overall vs By Category */}
        <div
          className="flex gap-1 p-1 rounded-xl bg-gray-800/60 border border-gray-700"
          role="tablist"
          aria-label="Leaderboard view"
        >
          <button
            role="tab"
            aria-selected={view === 'overall'}
            onClick={() => setView('overall')}
            className={`relative flex-1 px-4 py-2 text-sm font-medium rounded-lg
                       transition-colors duration-150
                       ${
                         view === 'overall'
                           ? 'text-white'
                           : 'text-gray-400 hover:text-gray-300'
                       }`}
          >
            {view === 'overall' && (
              <motion.div
                layoutId="view-indicator"
                className="absolute inset-0 bg-gray-700 rounded-lg"
                transition={{ type: 'spring', duration: 0.3, bounce: 0.15 }}
              />
            )}
            <span className="relative z-10">Overall</span>
          </button>
          <button
            role="tab"
            aria-selected={view === 'category'}
            onClick={() => setView('category')}
            className={`relative flex-1 px-4 py-2 text-sm font-medium rounded-lg
                       transition-colors duration-150
                       ${
                         view === 'category'
                           ? 'text-white'
                           : 'text-gray-400 hover:text-gray-300'
                       }`}
          >
            {view === 'category' && (
              <motion.div
                layoutId="view-indicator"
                className="absolute inset-0 bg-gray-700 rounded-lg"
                transition={{ type: 'spring', duration: 0.3, bounce: 0.15 }}
              />
            )}
            <span className="relative z-10">By Category</span>
          </button>
        </div>

        {/* Conditional View Content */}
        {view === 'overall' ? (
          <>
            {/* Scope Selector */}
            <ScopeSelector scope={scope} onScopeChange={setScope} />

            {/* Leaderboard Table */}
            <LeaderboardTable entries={entries} loading={loading} error={error} />
          </>
        ) : (
          <CategoryLeaderboard />
        )}
      </motion.div>
    </div>
  );
}
