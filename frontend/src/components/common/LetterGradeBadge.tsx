import { motion } from 'framer-motion';
import type { LetterGrade } from '../../types';

interface LetterGradeBadgeProps {
  grade: LetterGrade;
  distance: number;
  /** Optional size variant */
  size?: 'sm' | 'md' | 'lg';
}

/** Maps letter grades to styling */
const GRADE_STYLES: Record<LetterGrade, { bg: string; text: string; glow: string }> = {
  S: { bg: 'bg-yellow-400', text: 'text-yellow-900', glow: 'shadow-yellow-400/50' },
  A: { bg: 'bg-green-500', text: 'text-green-900', glow: 'shadow-green-500/40' },
  B: { bg: 'bg-blue-500', text: 'text-blue-900', glow: 'shadow-blue-500/40' },
  C: { bg: 'bg-orange-500', text: 'text-orange-900', glow: 'shadow-orange-500/40' },
  D: { bg: 'bg-red-500', text: 'text-red-900', glow: 'shadow-red-500/40' },
};

const SIZE_CLASSES = {
  sm: 'w-12 h-12 text-xl',
  md: 'w-20 h-20 text-4xl',
  lg: 'w-28 h-28 text-6xl',
};

/**
 * Animated letter grade badge displayed on the Reveal Screen.
 * Uses Framer Motion for a scale-in + glow entrance animation.
 */
export function LetterGradeBadge({ grade, distance, size = 'lg' }: LetterGradeBadgeProps) {
  const styles = GRADE_STYLES[grade];
  const sizeClass = SIZE_CLASSES[size];

  return (
    <div className="flex flex-col items-center gap-2">
      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{
          type: 'spring',
          stiffness: 200,
          damping: 15,
          delay: 0.2,
        }}
        className={`
          ${sizeClass} ${styles.bg} ${styles.text} ${styles.glow}
          rounded-full flex items-center justify-center
          font-black shadow-lg
        `}
        role="img"
        aria-label={`Grade ${grade}, ${distance} swap${distance !== 1 ? 's' : ''} from consensus`}
      >
        {grade}
      </motion.div>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="text-gray-400 text-sm"
      >
        {distance === 0
          ? 'Perfect match!'
          : `${distance} swap${distance !== 1 ? 's' : ''} from consensus`}
      </motion.p>
    </div>
  );
}
