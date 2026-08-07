import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Roll } from '../types';

export interface UseDailyReturn {
  /** Today's daily challenge Roll, or null if not yet loaded */
  roll: Roll | null;
  /** Whether the Roll is currently being fetched */
  loading: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Whether the user has already completed today's challenge */
  alreadyCompleted: boolean;
  /** The existing ranking ID if user already submitted today */
  existingRankingId: number | null;
  /** Refetch the daily challenge */
  refetch: () => void;
}

/**
 * Hook for fetching and caching the daily challenge Roll.
 * Handles duplicate submission detection — if the user has already submitted
 * today's ranking, it surfaces the existing ranking ID so the caller can
 * redirect to the reveal page.
 */
export function useDaily(): UseDailyReturn {
  const navigate = useNavigate();
  const [roll, setRoll] = useState<Roll | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [alreadyCompleted, setAlreadyCompleted] = useState(false);
  const [existingRankingId, setExistingRankingId] = useState<number | null>(null);
  const cacheRef = useRef<{ roll: Roll; date: string } | null>(null);

  const fetchDaily = useCallback(async () => {
    // Check in-memory cache: reuse if same UTC day
    const today = new Date().toISOString().split('T')[0];
    if (cacheRef.current && cacheRef.current.date === today) {
      setRoll(cacheRef.current.roll);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setAlreadyCompleted(false);
    setExistingRankingId(null);

    try {
      const response = await api.get<Roll>('/api/daily');
      setRoll(response.data);
      cacheRef.current = { roll: response.data, date: today };
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as {
          response?: { status?: number; data?: { detail?: string; ranking_id?: number } };
        };

        if (axiosErr.response?.status === 409) {
          // User already submitted today's challenge
          setAlreadyCompleted(true);
          const rankingId = axiosErr.response?.data?.ranking_id ?? null;
          setExistingRankingId(rankingId);

          // Auto-redirect to reveal if we have the ranking ID
          if (rankingId) {
            navigate(`/reveal/${rankingId}`);
          }
        } else if (axiosErr.response?.status === 401) {
          setError('Sign in to play the Daily Challenge.');
        } else {
          setError('Failed to load today\'s challenge. Please try again.');
        }
      } else {
        setError('Failed to load today\'s challenge. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchDaily();
  }, [fetchDaily]);

  return {
    roll,
    loading,
    error,
    alreadyCompleted,
    existingRankingId,
    refetch: fetchDaily,
  };
}
