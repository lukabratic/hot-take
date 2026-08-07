import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { motion } from 'framer-motion';
import type { Player } from '../../types';

interface PlayerCardProps {
  player: Player;
  rank: number;
}

/**
 * A draggable player card used in the ranking list.
 * Uses @dnd-kit useSortable for drag-and-drop and Framer Motion for animations.
 */
export function PlayerCard({ player, rank }: PlayerCardProps) {
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

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`
        flex items-center gap-4 p-4 rounded-lg border
        bg-gray-800 border-gray-700
        cursor-grab active:cursor-grabbing
        select-none
        ${isDragging ? 'z-50 shadow-xl shadow-nba-gold/20 border-nba-gold scale-[1.02]' : ''}
      `}
      {...attributes}
      {...listeners}
    >
      {/* Rank number */}
      <span
        className="flex-shrink-0 w-8 h-8 flex items-center justify-center
                   rounded-full bg-nba-blue text-white font-bold text-sm"
        aria-label={`Rank ${rank}`}
      >
        {rank}
      </span>

      {/* Player thumbnail placeholder */}
      <div
        className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-600
                   flex items-center justify-center text-xs font-medium text-gray-300"
        aria-hidden="true"
      >
        {player.name.split(' ').map((n) => n[0]).join('')}
      </div>

      {/* Player info */}
      <div className="flex-1 min-w-0">
        <p className="text-white font-semibold truncate">{player.name}</p>
        <p className="text-gray-400 text-sm">
          {player.position} · {player.era}
        </p>
      </div>

      {/* Drag handle indicator */}
      <div className="flex-shrink-0 text-gray-500" aria-hidden="true">
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
