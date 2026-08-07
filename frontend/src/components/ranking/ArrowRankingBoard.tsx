import { motion, AnimatePresence } from 'framer-motion';
import type { Player, ThemeModifier } from '../../types';

interface ArrowRankingBoardProps {
  items: Player[];
  onMoveUp: (index: number) => void;
  onMoveDown: (index: number) => void;
  variant?: 'default' | 'hoopiq';
  themeModifier?: ThemeModifier;
}

/**
 * Arrow-based ranking board. Each player card has up/down arrow buttons
 * for reordering. Simpler and more accessible than drag-and-drop.
 */
export function ArrowRankingBoard({
  items,
  onMoveUp,
  onMoveDown,
  variant = 'default',
}: ArrowRankingBoardProps) {
  return (
    <div className="flex flex-col gap-2" role="list" aria-label="Player ranking">
      <AnimatePresence>
        {items.map((player, index) => (
          <motion.div
            key={player.id}
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-3 p-3 rounded-lg border bg-gray-800 border-gray-700"
          >
            {/* Rank number */}
            <span
              className="flex-shrink-0 w-8 h-8 flex items-center justify-center
                         rounded-full bg-nba-blue text-white font-bold text-sm"
            >
              {index + 1}
            </span>

            {/* Player thumbnail */}
            <div
              className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-600
                         flex items-center justify-center text-xs font-medium text-gray-300"
            >
              {variant === 'hoopiq'
                ? '?'
                : player.name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')}
            </div>

            {/* Player info */}
            <div className="flex-1 min-w-0">
              <p className="text-white font-semibold truncate text-sm">
                {variant === 'hoopiq' ? `Player ${index + 1}` : player.name}
              </p>
              <p className="text-gray-400 text-xs">
                {player.position} · {player.era}
              </p>
            </div>

            {/* Arrow buttons */}
            <div className="flex flex-col gap-1 flex-shrink-0">
              <button
                onClick={() => onMoveUp(index)}
                disabled={index === 0}
                className="w-7 h-7 flex items-center justify-center rounded
                           bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white
                           disabled:opacity-30 disabled:cursor-not-allowed
                           transition-colors"
                aria-label={`Move ${player.name} up`}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                  <path d="M6 2L11 8H1L6 2Z" />
                </svg>
              </button>
              <button
                onClick={() => onMoveDown(index)}
                disabled={index === items.length - 1}
                className="w-7 h-7 flex items-center justify-center rounded
                           bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white
                           disabled:opacity-30 disabled:cursor-not-allowed
                           transition-colors"
                aria-label={`Move ${player.name} down`}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                  <path d="M6 10L1 4H11L6 10Z" />
                </svg>
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
