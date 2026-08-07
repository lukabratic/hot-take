import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';
import { motion } from 'framer-motion';
import { StreakCounter } from '../components/common/StreakCounter';

/**
 * Home page at route `/`
 * Displays the daily challenge call-to-action, mode selector for Quick Play
 * and HoopIQ, and the user's streak counter when authenticated.
 *
 * Requirements: 2.1, 11.3
 */
export function Home() {
  const navigate = useNavigate();
  const { isSignedIn } = useAuth();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md space-y-8 text-center"
      >
        {/* Logo / Title */}
        <header className="space-y-2">
          <h1 className="text-5xl font-bold text-nba-gold tracking-tight">
            Hot Take
          </h1>
          <p className="text-lg text-gray-400">NBA Ranking Game</p>
        </header>

        {/* Streak Counter (shown when authenticated) */}
        {isSignedIn && <StreakCounter />}

        {/* Daily Challenge CTA */}
        <motion.div
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        >
          <button
            onClick={() => navigate('/play/daily')}
            className="w-full py-4 px-6 rounded-xl bg-nba-gold text-gray-900 font-bold text-lg
                       shadow-lg shadow-nba-gold/20 hover:shadow-nba-gold/40
                       hover:scale-[1.02] active:scale-[0.98] transition-all duration-150"
            aria-label="Play today's daily challenge"
          >
            🏀 Play Today&apos;s Challenge
          </button>
        </motion.div>

        {/* Mode Selector */}
        <div className="space-y-3">
          <p className="text-sm text-gray-500 uppercase tracking-wide font-medium">
            Or choose a mode
          </p>
          <div className="grid grid-cols-2 gap-3">
            <ModeCard
              title="Quick Play"
              description="Unlimited random rounds"
              emoji="⚡"
              onClick={() => navigate('/play/quickplay')}
            />
            <ModeCard
              title="HoopIQ"
              description="Stats only, no names"
              emoji="🧠"
              onClick={() => navigate('/play/hoopiq')}
            />
          </div>
        </div>

        {/* Sign-in prompt for unauthenticated users */}
        {!isSignedIn && (
          <p className="text-sm text-gray-500">
            <Link to="/sign-in" className="text-nba-gold hover:underline">
              Sign in
            </Link>{' '}
            to track your streak and compete on the leaderboard.
          </p>
        )}
      </motion.div>
    </div>
  );
}

/** A mode selection card */
function ModeCard({
  title,
  description,
  emoji,
  onClick,
}: {
  title: string;
  description: string;
  emoji: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center gap-2 p-4 rounded-xl
                 bg-gray-800/60 border border-gray-700 hover:border-gray-500
                 hover:bg-gray-800 transition-all duration-150
                 active:scale-[0.97]"
      aria-label={`Play ${title} mode`}
    >
      <span className="text-2xl" aria-hidden="true">
        {emoji}
      </span>
      <span className="text-white font-semibold text-sm">{title}</span>
      <span className="text-gray-400 text-xs">{description}</span>
    </button>
  );
}
