import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import type { LeaderboardScope, LeaderboardEntry } from '../types';

interface UseLeaderboardResult {
  entries: LeaderboardEntry[];
  loading: boolean;
  error: string | null;
  scope: LeaderboardScope;
  setScope: (scope: LeaderboardScope) => void;
  refresh: () => void;
}

/**
 * Hook for fetching and managing leaderboard data.
 * Supports scope switching between today, week, alltime, and friends.
 *
 * Requirements: 12.1, 12.2
 */
export function useLeaderboard(
  initialScope: LeaderboardScope = 'today'
): UseLeaderboardResult {
  const [scope, setScope] = useState<LeaderboardScope>(initialScope);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLeaderboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.get<{
        scope: string;
        entries: Array<{
          rank: number;
          user_id: string;
          username: string;
          score: number;
          current_streak: number;
        }>;
      }>('/api/leaderboard', { params: { scope } });

      // Map snake_case response to camelCase
      const mapped: LeaderboardEntry[] = res.data.entries.map((e) => ({
        rank: e.rank,
        userId: e.user_id,
        username: e.username,
        score: e.score,
        currentStreak: e.current_streak,
      }));

      setEntries(mapped);
    } catch (err: unknown) {
      setError('Failed to load leaderboard');
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);

  return {
    entries,
    loading,
    error,
    scope,
    setScope,
    refresh: fetchLeaderboard,
  };
}
