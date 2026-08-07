import { motion } from 'framer-motion';
import type { Player, PlayerStats, ThemeModifier } from '../../types';

interface HoopIQComparisonViewProps {
  /** Player objects keyed by ID for lookup */
  playersById: Record<number, Player>;
  /** User's submitted ranking (player IDs in order) */
  userOrder: number[];
  /** System consensus ranking (player IDs in order) */
  consensusOrder: number[];
  /** Theme modifier to determine which stats to show */
  themeModifier?: ThemeModifier;
}

/**
 * Returns the appropriate stats object based on the theme modifier.
 */
function getStatsForTheme(player: Player, themeModifier?: ThemeModifier): PlayerStats {
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
 * HoopIQ-specific comparison view for the Reveal screen.
 * The key experience: player NAMES are revealed alongside their stat lines
 * with a staggered animation — this is the "name reveal" moment.
 */
export function HoopIQComparisonView({
  playersById,
  userOrder,
  consensusOrder,
  themeModifier,
}: HoopIQComparisonViewProps) {
  return (
    <div className="w-full space-y-3">
      <h3 className="text-sm font-semibold text-purple-300 uppercase tracking-wide text-center">
        🧠 Name Reveal — Who Was Who?
      </h3>

      {/* Column headers */}
      <div className="grid grid-cols-[1.5rem_1fr_auto] gap-2 px-2">
        <span className="text-xs text-gray-500">#</span>
        <span className="text-xs text-purple-300 font-medium">Consensus Ranking</span>
        <span className="text-xs text-gray-400 font-medium">Your Pick</span>
      </div>

      {/* Rows — ordered by consensus */}
      {consensusOrder.map((playerId, idx) => {
        const player = playersById[playerId];
        const userRank = userOrder.indexOf(playerId) + 1;
        const isMatch = userRank === idx + 1;
        const stats = player ? getStatsForTheme(player, themeModifier) : null;

        return (
          <motion.div
            key={playerId}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + 0.15 * idx, duration: 0.4 }}
            className={`
              grid grid-cols-[1.5rem_1fr_auto] gap-2 items-center px-3 py-3 rounded-lg
              ${isMatch
                ? 'bg-green-900/20 border border-green-700/40'
                : 'bg-amber-900/20 border border-amber-700/40'}
            `}
          >
            {/* Rank number */}
            <span className="text-sm font-bold text-purple-300">{idx + 1}</span>

            {/* Player info — NAME REVEALED */}
            <div className="min-w-0">
              <motion.div
                initial={{ opacity: 0, filter: 'blur(8px)' }}
                animate={{ opacity: 1, filter: 'blur(0px)' }}
                transition={{ delay: 0.6 + 0.15 * idx, duration: 0.5 }}
                className="flex items-center gap-2 mb-1"
              >
                <span className="text-white font-semibold text-sm truncate">
                  {player?.name ?? 'Unknown'}
                </span>
                {player?.era && (
                  <span className="text-gray-500 text-xs flex-shrink-0">
                    {player.era}
                  </span>
                )}
              </motion.div>

              {/* Stat line */}
              {stats && (
                <div className="flex flex-wrap gap-x-2 text-xs text-gray-400">
                  <span>{stats.pts.toFixed(1)} PTS</span>
                  <span>{stats.reb.toFixed(1)} REB</span>
                  <span>{stats.ast.toFixed(1)} AST</span>
                  <span className="text-gray-500">{stats.per.toFixed(1)} PER</span>
                </div>
              )}
            </div>

            {/* User's rank for this player */}
            <div className="flex-shrink-0 flex items-center gap-1">
              {isMatch ? (
                <span className="text-green-400 text-xs font-medium">✓</span>
              ) : (
                <span className="text-amber-400 text-xs font-medium">
                  You: #{userRank}
                </span>
              )}
            </div>
          </motion.div>
        );
      })}

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 pt-1 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-green-600" />
          Matched
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-600" />
          Differs
        </span>
      </div>
    </div>
  );
}
