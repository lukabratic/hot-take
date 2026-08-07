import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { motion } from 'framer-motion';
import api from '../../services/api';

interface StreakData {
  current_streak: number;
  longest_streak: number;
}

interface StreakCounterProps {
  /** Optional class name for the container */
  className?: string;
}

/**
 * Streak counter component that displays a flame icon and current
 * streak count. Fetches data from GET /api/streak when authenticated.
 *
 * Requirements: 11.3
 */
export function StreakCounter({ className = '' }: StreakCounterProps) {
  const { isSignedIn } = useAuth();
  const [streak, setStreak] = useState<StreakData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isSignedIn) {
      setStreak(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    api
      .get<StreakData>('/api/streak')
      .then((res) => {
        if (!cancelled) setStreak(res.data);
      })
      .catch(() => {
        // Streak display is non-critical; fail silently
        if (!cancelled) setStreak(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isSignedIn]);

  // Don't render anything if not signed in
  if (!isSignedIn) {
    return null;
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center gap-2 py-2 ${className}`}>
        <div
          className="h-4 w-4 border-2 border-nba-gold border-t-transparent rounded-full animate-spin"
          role="status"
          aria-label="Loading streak data"
        />
        <span className="text-sm text-gray-500">Loading streak…</span>
      </div>
    );
  }

  if (!streak || streak.current_streak === 0) {
    return (
      <div className={`py-2 ${className}`}>
        <p className="text-sm text-gray-500">
          Start a streak by completing today&apos;s challenge!
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full
                 bg-orange-500/10 border border-orange-500/30 ${className}`}
      aria-label={`Current streak: ${streak.current_streak} day${streak.current_streak !== 1 ? 's' : ''}`}
    >
      <span className="text-xl" aria-hidden="true">
        🔥
      </span>
      <span className="text-orange-400 font-bold text-lg">
        {streak.current_streak}
      </span>
      <span className="text-gray-400 text-sm">
        day{streak.current_streak !== 1 ? 's' : ''} streak
      </span>
    </motion.div>
  );
}
