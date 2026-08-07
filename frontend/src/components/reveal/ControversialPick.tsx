import { motion } from 'framer-motion';
import type { ControversialPick as ControversialPickType, Player } from '../../types';

interface ControversialPickProps {
  /** The controversial pick data */
  pick: ControversialPickType;
  /** Player objects keyed by ID for lookup */
  playersById: Record<number, Player>;
}

/**
 * Highlights the user's most controversial pick — the placement with the
 * lowest community agreement percentage.
 */
export function ControversialPick({ pick, playersById }: ControversialPickProps) {
  const player = playersById[pick.playerId];
  const playerName = player?.name ?? 'Unknown Player';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.6, type: 'spring', stiffness: 200, damping: 20 }}
      className="w-full p-4 rounded-lg bg-red-900/20 border border-red-700/40"
    >
      <div className="flex items-start gap-3">
        {/* Fire icon */}
        <span className="text-2xl flex-shrink-0" aria-hidden="true">
          🔥
        </span>

        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-red-300 uppercase tracking-wide">
            Hot Take Alert
          </h3>

          <p className="text-white mt-1">
            You ranked{' '}
            <span className="font-bold text-red-200">{playerName}</span>
            {' '}at #{pick.slot}
          </p>

          <p className="text-gray-400 text-sm mt-1">
            Only{' '}
            <span className="font-semibold text-red-300">
              {pick.communityAgreement.toFixed(1)}%
            </span>
            {' '}of players put them there
          </p>
        </div>
      </div>
    </motion.div>
  );
}
