import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { motion } from 'framer-motion';
import type { Player, PlayerStats, ThemeModifier } from '../../types';

interface HoopIQPlayerCardProps {
  player: Player;
  rank: number;
  themeModifier: ThemeModifier;
}

/**
 * Returns the appropriate stats object based on the theme modifier.
 * - "Peak Season Only" → peakStats
 * - "Playoff Performance" → playoffStats (falls back to careerStats if null)
 * - All others → careerStats
 */
function getStatsForTheme(player: Player, themeModifier: ThemeModifier): PlayerStats {
  switch (themeModifier) {
    case 'Peak Season Only':
      return player.peakStats;
    case 'Playoff Performance':
      return player.playoffStats ?? player.careerStats;
    default:
      return player.careerStats;
  }
}

/**
 * Returns a human-readable label for the stat source being displayed.
 */
function getStatsLabel(themeModifier: ThemeModifier): string {
  switch (themeModifier) {
    case 'Peak Season Only':
      return 'Peak Season';
    case 'Playoff Performance':
      return 'Playoff Career';
    default:
      return 'Career';
  }
}

/**
 * A stat-line-only variant of PlayerCard used in HoopIQ mode.
 * Hides player name, photo/initials, position, era, and team info.
 * Shows only statistical lines based on the theme modifier to test
 * pure basketball analytics knowledge.
 */
export function HoopIQPlayerCard({ player, rank, themeModifier }: HoopIQPlayerCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: player.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const stats = getStatsForTheme(player, themeModifier);
  const statsLabel = getStatsLabel(themeModifier);

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`
        flex items-center gap-3 p-4 rounded-lg border
        bg-gray-900 border-purple-700/50
        cursor-grab active:cursor-grabbing
        select-none
        ${isDragging ? 'z-50 shadow-xl shadow-purple-500/30 border-purple-500 scale-[1.02]' : ''}
      `}
      {...attributes}
      {...listeners}
    >
      {/* Rank number */}
      <span
        className="flex-shrink-0 w-8 h-8 flex items-center justify-center
                   rounded-full bg-purple-600 text-white font-bold text-sm"
        aria-label={`Rank ${rank}`}
      >
        {rank}
      </span>

      {/* Mystery player icon */}
      <div
        className="flex-shrink-0 w-10 h-10 rounded-full bg-purple-900/60 border border-purple-500/40
                   flex items-center justify-center"
        aria-hidden="true"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-purple-300"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      </div>

      {/* Stats display */}
      <div className="flex-1 min-w-0">
        {/* Label row */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-purple-300 text-xs font-medium uppercase tracking-wide">
            Player {String.fromCharCode(64 + rank)}
          </span>
          <span className="text-gray-500 text-xs">·</span>
          <span className="text-gray-500 text-xs">{statsLabel} Stats</span>
        </div>

        {/* Primary stats row */}
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-sm">
          <StatChip label="PTS" value={stats.pts} />
          <StatChip label="REB" value={stats.reb} />
          <StatChip label="AST" value={stats.ast} />
          <StatChip label="STL" value={stats.stl} />
          <StatChip label="BLK" value={stats.blk} />
        </div>

        {/* Advanced stats row */}
        <div className="flex flex-wrap gap-x-3 mt-0.5 text-xs">
          <StatChip label="PER" value={stats.per} advanced />
          <StatChip label="BPM" value={stats.bpm} advanced />
        </div>
      </div>

      {/* Drag handle indicator */}
      <div className="flex-shrink-0 text-purple-400/50" aria-hidden="true">
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="currentColor"
          className="opacity-50"
        >
          <circle cx="5" cy="3" r="1.5" />
          <circle cx="11" cy="3" r="1.5" />
          <circle cx="5" cy="8" r="1.5" />
          <circle cx="11" cy="8" r="1.5" />
          <circle cx="5" cy="13" r="1.5" />
          <circle cx="11" cy="13" r="1.5" />
        </svg>
      </div>
    </motion.div>
  );
}

/** Small chip displaying a stat label and value */
function StatChip({ label, value, advanced }: { label: string; value: number; advanced?: boolean }) {
  return (
    <span className={advanced ? 'text-gray-400' : 'text-gray-200'}>
      <span className={`font-medium ${advanced ? 'text-gray-500' : 'text-gray-400'}`}>
        {label}
      </span>{' '}
      {value.toFixed(1)}
    </span>
  );
}
