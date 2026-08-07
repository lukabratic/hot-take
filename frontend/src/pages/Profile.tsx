import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import type { ProfileStats, ProfileRankingHistoryEntry } from '../types';

/**
 * Profile page at route `/profile`.
 * Displays user stats summary, grade distribution, streak info,
 * and recent ranking history.
 *
 * Requirements: 14.1
 */
export function Profile() {
  const { isSignedIn, isLoaded } = useAuth();
  const [profile, setProfile] = useState<ProfileStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;

    async function fetchProfile() {
      try {
        setLoading(true);
        const response = await api.get('/api/profile');
        const data = response.data;
        // Map snake_case from API to camelCase
        setProfile({
          id: data.id,
          username: data.username,
          avatarUrl: data.avatar_url,
          totalGames: data.total_games,
          averageGrade: data.average_grade,
          bestGrade: data.best_grade,
          currentStreak: data.current_streak,
          longestStreak: data.longest_streak,
          gradeDistribution: data.grade_distribution,
          recentHistory: (data.recent_history || []).map(
            (entry: Record<string, unknown>) => ({
              id: entry.id as number,
              rollPosition: entry.roll_position as string,
              rollThemeModifier: entry.roll_theme_modifier as string,
              letterGrade: entry.letter_grade as ProfileRankingHistoryEntry['letterGrade'],
              mode: entry.mode as ProfileRankingHistoryEntry['mode'],
              rubric: entry.rubric as ProfileRankingHistoryEntry['rubric'],
              kendallTauDistance: entry.kendall_tau_distance as number,
              createdAt: entry.created_at as string,
            })
          ),
        });
      } catch {
        setError('Failed to load profile. Please try again.');
      } finally {
        setLoading(false);
      }
    }

    fetchProfile();
  }, [isLoaded, isSignedIn]);

  if (!isLoaded) {
    return <LoadingState />;
  }

  if (!isSignedIn) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <p className="text-gray-400 text-lg">
          <Link to="/sign-in" className="text-nba-gold hover:underline">
            Sign in
          </Link>{' '}
          to view your profile.
        </p>
      </div>
    );
  }

  if (loading) {
    return <LoadingState />;
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <p className="text-red-400">{error || 'Something went wrong.'}</p>
        <Link to="/" className="mt-4 text-nba-gold hover:underline">
          ← Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-4 pt-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-lg space-y-6"
      >
        {/* Header */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {profile.avatarUrl && (
              <img
                src={profile.avatarUrl}
                alt={`${profile.username}'s avatar`}
                className="w-12 h-12 rounded-full border-2 border-nba-gold"
              />
            )}
            <div>
              <h1 className="text-2xl font-bold text-white">{profile.username}</h1>
              <p className="text-sm text-gray-400">Your hot takes profile</p>
            </div>
          </div>
          <Link
            to="/"
            className="text-sm text-nba-gold hover:underline"
            aria-label="Back to home"
          >
            ← Home
          </Link>
        </header>

        {/* Stats Summary */}
        <StatsGrid profile={profile} />

        {/* Grade Distribution */}
        <GradeDistribution distribution={profile.gradeDistribution} totalGames={profile.totalGames} />

        {/* Streak Info */}
        <StreakInfo currentStreak={profile.currentStreak} longestStreak={profile.longestStreak} />

        {/* Ranking History */}
        <RankingHistory history={profile.recentHistory} />
      </motion.div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="animate-pulse text-gray-400">Loading profile...</div>
    </div>
  );
}

function StatsGrid({ profile }: { profile: ProfileStats }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.1 }}
      className="grid grid-cols-3 gap-3"
    >
      <StatCard label="Games" value={String(profile.totalGames)} />
      <StatCard label="Avg Grade" value={profile.averageGrade.toFixed(1)} />
      <StatCard label="Best" value={profile.bestGrade} />
    </motion.div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center p-3 rounded-xl bg-gray-800/60 border border-gray-700">
      <span className="text-xl font-bold text-white">{value}</span>
      <span className="text-xs text-gray-400 mt-1">{label}</span>
    </div>
  );
}

function GradeDistribution({
  distribution,
  totalGames,
}: {
  distribution: Record<string, number>;
  totalGames: number;
}) {
  if (totalGames === 0) return null;

  const grades = ['S', 'A', 'B', 'C', 'D'];
  const gradeColors: Record<string, string> = {
    S: 'bg-yellow-400',
    A: 'bg-green-400',
    B: 'bg-blue-400',
    C: 'bg-orange-400',
    D: 'bg-red-400',
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2 }}
      className="p-4 rounded-xl bg-gray-800/60 border border-gray-700 space-y-3"
    >
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        Grade Distribution
      </h2>
      <div className="space-y-2">
        {grades.map((grade) => {
          const count = distribution[grade] || 0;
          const percentage = totalGames > 0 ? (count / totalGames) * 100 : 0;
          return (
            <div key={grade} className="flex items-center gap-2">
              <span className="w-4 text-xs font-bold text-gray-300">{grade}</span>
              <div className="flex-1 h-4 bg-gray-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ delay: 0.3, duration: 0.5 }}
                  className={`h-full rounded-full ${gradeColors[grade]}`}
                />
              </div>
              <span className="w-8 text-xs text-gray-400 text-right">{count}</span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

function StreakInfo({
  currentStreak,
  longestStreak,
}: {
  currentStreak: number;
  longestStreak: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="flex gap-3"
    >
      <div className="flex-1 flex flex-col items-center p-3 rounded-xl bg-gray-800/60 border border-gray-700">
        <span className="text-2xl" aria-hidden="true">🔥</span>
        <span className="text-lg font-bold text-white">{currentStreak}</span>
        <span className="text-xs text-gray-400">Current Streak</span>
      </div>
      <div className="flex-1 flex flex-col items-center p-3 rounded-xl bg-gray-800/60 border border-gray-700">
        <span className="text-2xl" aria-hidden="true">🏆</span>
        <span className="text-lg font-bold text-white">{longestStreak}</span>
        <span className="text-xs text-gray-400">Longest Streak</span>
      </div>
    </motion.div>
  );
}

function RankingHistory({ history }: { history: ProfileRankingHistoryEntry[] }) {
  if (history.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-gray-800/60 border border-gray-700 text-center">
        <p className="text-gray-400 text-sm">No games played yet. Start a challenge!</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.4 }}
      className="space-y-3"
    >
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        Recent Games
      </h2>
      <div className="space-y-2">
        {history.map((entry) => (
          <HistoryEntry key={entry.id} entry={entry} />
        ))}
      </div>
    </motion.div>
  );
}

function HistoryEntry({ entry }: { entry: ProfileRankingHistoryEntry }) {
  const gradeColors: Record<string, string> = {
    S: 'text-yellow-400',
    A: 'text-green-400',
    B: 'text-blue-400',
    C: 'text-orange-400',
    D: 'text-red-400',
  };

  const formattedDate = new Date(entry.createdAt).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });

  return (
    <Link
      to={`/reveal/${entry.id}`}
      className="flex items-center justify-between p-3 rounded-xl bg-gray-800/60 border border-gray-700
                 hover:border-gray-500 transition-colors"
    >
      <div className="flex items-center gap-3">
        <span className={`text-lg font-bold ${gradeColors[entry.letterGrade] || 'text-gray-300'}`}>
          {entry.letterGrade}
        </span>
        <div>
          <p className="text-sm text-white font-medium">
            {entry.rollPosition} · {entry.rollThemeModifier}
          </p>
          <p className="text-xs text-gray-400">
            {entry.mode} · {entry.rubric} · {formattedDate}
          </p>
        </div>
      </div>
      <span className="text-xs text-gray-500">{entry.kendallTauDistance} swaps</span>
    </Link>
  );
}
