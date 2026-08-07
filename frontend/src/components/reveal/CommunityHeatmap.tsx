import { motion } from 'framer-motion';
import type { CommunityHeatmap as CommunityHeatmapType, Player } from '../../types';

interface CommunityHeatmapProps {
  /** Community heatmap data (player_id -> slot -> percentage) */
  heatmap: CommunityHeatmapType;
  /** Player objects keyed by ID for lookup */
  playersById: Record<number, Player>;
  /** User's submitted ranking order (player IDs) */
  userOrder: number[];
}

/**
 * Displays a grid of percentages showing where the community placed each player.
 * Highlights the user's placement in each slot with a border ring.
 */
export function CommunityHeatmap({
  heatmap,
  playersById,
  userOrder,
}: CommunityHeatmapProps) {
  const slotCount = userOrder.length;
  const playerIds = userOrder;

  // Get the user's placement mapping: playerId -> slot (1-indexed)
  const userPlacement: Record<number, number> = {};
  userOrder.forEach((pid, idx) => {
    userPlacement[pid] = idx + 1;
  });

  if (heatmap.totalSubmissions === 0) {
    return (
      <div className="w-full text-center py-4">
        <p className="text-gray-500 text-sm">
          Be the first to submit — community data will appear after more responses.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-3">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide text-center">
        Community Heatmap
      </h3>

      <p className="text-xs text-gray-500 text-center">
        {heatmap.totalSubmissions} submission{heatmap.totalSubmissions !== 1 ? 's' : ''}
      </p>

      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs" role="grid" aria-label="Community placement heatmap">
          <thead>
            <tr>
              <th className="text-left text-gray-500 font-medium py-1 px-1 w-24">Player</th>
              {Array.from({ length: slotCount }, (_, i) => (
                <th key={i} className="text-center text-gray-500 font-medium py-1 px-1">
                  #{i + 1}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {playerIds.map((playerId, rowIdx) => {
              const player = playersById[playerId];
              const playerData = heatmap.data[playerId] ?? {};

              return (
                <motion.tr
                  key={playerId}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.05 * rowIdx }}
                >
                  <td className="text-gray-300 font-medium py-1.5 px-1 truncate max-w-[6rem]">
                    {player?.name.split(' ').pop() ?? 'Unknown'}
                  </td>
                  {Array.from({ length: slotCount }, (_, slotIdx) => {
                    const slot = slotIdx + 1;
                    const percentage = playerData[slot] ?? 0;
                    const isUserPlacement = userPlacement[playerId] === slot;
                    const intensity = getIntensityClass(percentage);

                    return (
                      <td key={slotIdx} className="text-center py-1.5 px-0.5">
                        <span
                          className={`
                            inline-block w-full py-1 rounded
                            ${intensity}
                            ${isUserPlacement ? 'ring-2 ring-nba-gold ring-offset-1 ring-offset-gray-900' : ''}
                          `}
                          aria-label={`${player?.name ?? 'Unknown'} in slot ${slot}: ${percentage}% of community${isUserPlacement ? ' (your pick)' : ''}`}
                        >
                          {percentage > 0 ? `${percentage}%` : '—'}
                        </span>
                      </td>
                    );
                  })}
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-2 text-[10px] text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded ring-2 ring-nba-gold ring-offset-1 ring-offset-gray-900" />
          Your pick
        </span>
      </div>
    </div>
  );
}

/** Returns a Tailwind background class based on the percentage intensity. */
function getIntensityClass(percentage: number): string {
  if (percentage >= 60) return 'bg-green-700/60 text-green-100';
  if (percentage >= 40) return 'bg-green-800/40 text-green-200';
  if (percentage >= 20) return 'bg-gray-700/60 text-gray-200';
  if (percentage > 0) return 'bg-gray-800/60 text-gray-400';
  return 'bg-gray-900/40 text-gray-600';
}
