import { motion } from 'framer-motion';
import type { Player } from '../../types';

interface ComparisonViewProps {
  /** Player objects keyed by ID for lookup */
  playersById: Record<number, Player>;
  /** User's submitted ranking (player IDs in order) */
  userOrder: number[];
  /** System consensus ranking (player IDs in order) */
  consensusOrder: number[];
}

/**
 * Side-by-side comparison of the user's ranking vs the consensus ranking.
 * Highlights differences with color coding: green for matches, amber for mismatches.
 */
export function ComparisonView({
  playersById,
  userOrder,
  consensusOrder,
}: ComparisonViewProps) {
  return (
    <div className="w-full space-y-3">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide text-center">
        Your Ranking vs Consensus
      </h3>

      {/* Column headers */}
      <div className="grid grid-cols-[1.5rem_1fr_1fr] gap-2 px-2">
        <span className="text-xs text-gray-500">#</span>
        <span className="text-xs text-gray-400 font-medium">You</span>
        <span className="text-xs text-gray-400 font-medium text-right">Consensus</span>
      </div>

      {/* Rows */}
      {userOrder.map((playerId, idx) => {
        const consensusPlayerId = consensusOrder[idx];
        const isMatch = playerId === consensusPlayerId;
        const userPlayer = playersById[playerId];
        const consensusPlayer = playersById[consensusPlayerId];

        return (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * idx }}
            className={`
              grid grid-cols-[1.5rem_1fr_1fr] gap-2 items-center px-2 py-2.5 rounded-lg
              ${isMatch
                ? 'bg-green-900/20 border border-green-700/40'
                : 'bg-amber-900/20 border border-amber-700/40'}
            `}
          >
            {/* Rank number */}
            <span className="text-xs font-bold text-gray-400">{idx + 1}</span>

            {/* User's pick */}
            <div className="flex items-center gap-2 min-w-0">
              <div
                className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-600
                           flex items-center justify-center text-[10px] font-medium text-gray-300"
                aria-hidden="true"
              >
                {userPlayer?.name.split(' ').map((n) => n[0]).join('') ?? '?'}
              </div>
              <span className="text-white text-sm font-medium truncate">
                {userPlayer?.name ?? 'Unknown'}
              </span>
            </div>

            {/* Consensus pick */}
            <div className="flex items-center gap-2 justify-end min-w-0">
              <span className="text-gray-300 text-sm truncate text-right">
                {consensusPlayer?.name ?? 'Unknown'}
              </span>
              <div
                className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-600
                           flex items-center justify-center text-[10px] font-medium text-gray-300"
                aria-hidden="true"
              >
                {consensusPlayer?.name.split(' ').map((n) => n[0]).join('') ?? '?'}
              </div>
            </div>
          </motion.div>
        );
      })}

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 pt-1 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-green-600" />
          Match
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-600" />
          Differs
        </span>
      </div>
    </div>
  );
}
