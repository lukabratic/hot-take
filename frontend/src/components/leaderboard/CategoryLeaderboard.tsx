import { motion } from 'framer-motion';
import { useCategoryLeaderboard } from '../../hooks/useCategoryLeaderboard';
import type { CategoryLeaderboardScope } from '../../hooks/useCategoryLeaderboard';
import type { CategoryType } from '../../types';
import type { CategoryLeaderboardEntry } from '../../services/api';

const CATEGORY_TYPES: { value: CategoryType; label: string }[] = [
  { value: 'position', label: 'Position' },
  { value: 'team', label: 'Team' },
  { value: 'decade', label: 'Decade' },
  { value: 'conference', label: 'Conference' },
];

const SCOPES: { value: CategoryLeaderboardScope; label: string }[] = [
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'alltime', label: 'All-Time' },
];

/**
 * Category leaderboard component.
 * Allows selecting a category type and value, switching scope,
 * and displays ranked entries with score and date.
 *
 * Requirements: 6.2, 6.3, 6.4
 */
export function CategoryLeaderboard() {
  const {
    entries,
    loading,
    error,
    scope,
    setScope,
    categoryType,
    setCategoryType,
    categoryValue,
    setCategoryValue,
    availableCategories,
    categoriesLoading,
  } = useCategoryLeaderboard('today');

  const currentValues = availableCategories[categoryType] || [];

  return (
    <div className="space-y-4">
      {/* Category Type Tabs */}
      <div
        className="flex gap-1 p-1 rounded-xl bg-gray-800/60 border border-gray-700"
        role="tablist"
        aria-label="Category type"
      >
        {CATEGORY_TYPES.map(({ value, label }) => (
          <button
            key={value}
            role="tab"
            aria-selected={categoryType === value}
            onClick={() => setCategoryType(value)}
            className={`relative flex-1 px-3 py-2 text-sm font-medium rounded-lg
                       transition-colors duration-150
                       ${
                         categoryType === value
                           ? 'text-white'
                           : 'text-gray-400 hover:text-gray-300'
                       }`}
          >
            {categoryType === value && (
              <motion.div
                layoutId="category-type-indicator"
                className="absolute inset-0 bg-gray-700 rounded-lg"
                transition={{ type: 'spring', duration: 0.3, bounce: 0.15 }}
              />
            )}
            <span className="relative z-10">{label}</span>
          </button>
        ))}
      </div>

      {/* Category Value Selector */}
      {categoriesLoading ? (
        <div className="flex items-center justify-center py-4">
          <div
            className="h-5 w-5 border-2 border-nba-gold border-t-transparent rounded-full animate-spin"
            role="status"
            aria-label="Loading categories"
          />
        </div>
      ) : (
        <div>
          <label htmlFor="category-value-select" className="sr-only">
            Select category value
          </label>
          <select
            id="category-value-select"
            value={categoryValue}
            onChange={(e) => setCategoryValue(e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg bg-gray-800 border border-gray-700
                       text-white text-sm font-medium
                       focus:outline-none focus:ring-2 focus:ring-nba-gold/50 focus:border-nba-gold
                       appearance-none cursor-pointer"
          >
            {currentValues.map((cv) => (
              <option key={cv.value} value={cv.value} disabled={cv.disabled}>
                {cv.label} ({cv.playerCount} players)
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Scope Toggle */}
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
            onClick={() => setScope(value)}
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
                layoutId="category-scope-indicator"
                className="absolute inset-0 bg-gray-700 rounded-lg"
                transition={{ type: 'spring', duration: 0.3, bounce: 0.15 }}
              />
            )}
            <span className="relative z-10">{label}</span>
          </button>
        ))}
      </div>

      {/* Entries Table */}
      <CategoryLeaderboardTable entries={entries} loading={loading} error={error} />
    </div>
  );
}

// ─── Internal Table Component ─────────────────────────────────────────────────

interface CategoryLeaderboardTableProps {
  entries: CategoryLeaderboardEntry[];
  loading: boolean;
  error: string | null;
}

function CategoryLeaderboardTable({ entries, loading, error }: CategoryLeaderboardTableProps) {
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
          No entries yet. Be the first to rank in this category!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2" role="table" aria-label="Category leaderboard rankings">
      {/* Header */}
      <div
        className="grid grid-cols-[3rem_1fr_5rem_5rem] gap-2 px-4 py-2 text-xs text-gray-500 uppercase tracking-wide font-medium"
        role="row"
      >
        <span role="columnheader">Rank</span>
        <span role="columnheader">Player</span>
        <span role="columnheader" className="text-right">Score</span>
        <span role="columnheader" className="text-right">Date</span>
      </div>

      {/* Entries */}
      {entries.map((entry, index) => (
        <motion.div
          key={`${entry.username}-${entry.rank}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.03, duration: 0.2 }}
          className="grid grid-cols-[3rem_1fr_5rem_5rem] gap-2 items-center px-4 py-3
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

          {/* Date */}
          <span role="cell" className="text-right text-gray-400 text-sm">
            {formatDate(entry.date)}
          </span>
        </motion.div>
      ))}
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

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

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}
