import { motion } from 'framer-motion';
import type { LeaderboardEntry } from '../../types';

interface LeaderboardTableProps {
  entries: LeaderboardEntry[];
  loading: boolean;
  error: string | null;
}

/**
 * Leaderboard table displaying ranked users with their score and streak.
 * Shows rank position, username, score, and current daily streak.
 *
 * Requirements: 12.1, 12.5
 */
export function LeaderboardTable({ entries, loading, error }: LeaderboardTableProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div
          className="h-6 w-6 border-2 border-nba-gold border-t-transparent rounded-full animate-spin"
          role="status"
          aria-label="Loading leaderboard"
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-sm">
          No entries yet. Be the first to rank!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2" role="table" aria-label="Leaderboard rankings">
      {/* Header */}
      <div
        className="grid grid-cols-[3rem_1fr_5rem_4rem] gap-2 px-4 py-2 text-xs text-gray-500 uppercase tracking-wide font-medium"
        role="row"
      >
        <span role="columnheader">Rank</span>
        <span role="columnheader">Player</span>
        <span role="columnheader" className="text-right">Score</span>
        <span role="columnheader" className="text-right">Streak</span>
      </div>

      {/* Entries */}
      {entries.map((entry, index) => (
        <motion.div
          key={entry.userId}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.03, duration: 0.2 }}
          className="grid grid-cols-[3rem_1fr_5rem_4rem] gap-2 items-center px-4 py-3
                     rounded-lg bg-gray-800/40 border border-gray-700/50
                     hover:bg-gray-800/70 transition-colors duration-100"
          role="row"
        >
          {/* Rank */}
          <span
            role="cell"
            className={`text-center font-bold text-lg ${getRankColor(entry.rank)}`}
          >
            {entry.rank <= 3 ? getRankEmoji(entry.rank) : entry.rank}
          </span>

          {/* Username */}
          <span role="cell" className="text-white font-medium truncate">
            {entry.username}
          </span>

          {/* Score */}
          <span role="cell" className="text-right text-nba-gold font-semibold">
            {entry.score.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>

          {/* Streak */}
          <span role="cell" className="text-right text-gray-400 text-sm">
            {entry.currentStreak > 0 && (
              <span className="inline-flex items-center gap-1">
                <span aria-hidden="true">🔥</span>
                {entry.currentStreak}
              </span>
            )}
          </span>
        </motion.div>
      ))}
    </div>
  );
}

function getRankColor(rank: number): string {
  switch (rank) {
    case 1:
      return 'text-yellow-400';
    case 2:
      return 'text-gray-300';
    case 3:
      return 'text-orange-400';
    default:
      return 'text-gray-500';
  }
}

function getRankEmoji(rank: number): string {
  switch (rank) {
    case 1:
      return '🥇';
    case 2:
      return '🥈';
    case 3:
      return '🥉';
    default:
      return String(rank);
  }
}
