import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import type {
  DebateSession,
  DebateComparison,
  DebateRoll,
  Rubric,
} from '../types';

export interface UseDebateReturn {
  /** The debate session metadata */
  session: DebateSession | null;
  /** The Roll and players for this debate */
  roll: DebateRoll | null;
  /** The full comparison data (available when status is 'complete') */
  comparison: DebateComparison | null;
  /** Whether data is currently loading */
  loading: boolean;
  /** Error message if something failed */
  error: string | null;
  /** Whether the current user has already submitted their ranking */
  hasSubmitted: boolean;
  /** Create a new debate session and return its ID */
  createSession: () => Promise<string | null>;
  /** Submit a ranking for this debate */
  submitRanking: (
    playerOrder: number[],
    rubric: Rubric
  ) => Promise<{ success: boolean; sessionStatus?: string }>;
  /** Refetch the session state */
  refetch: () => void;
}

/**
 * Hook for managing debate session state.
 * Handles creation, fetching session/roll data, submitting rankings,
 * and retrieving comparison results.
 */
export function useDebate(sessionId?: string): UseDebateReturn {
  const [session, setSession] = useState<DebateSession | null>(null);
  const [roll, setRoll] = useState<DebateRoll | null>(null);
  const [comparison, setComparison] = useState<DebateComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const fetchSession = useCallback(async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch session metadata
      const sessionRes = await api.get<DebateSession>(
        `/api/debate/${sessionId}`
      );
      const sessionData: DebateSession = {
        id: (sessionRes.data as any).id,
        rollId: (sessionRes.data as any).roll_id,
        creatorId: (sessionRes.data as any).creator_id,
        opponentId: (sessionRes.data as any).opponent_id,
        status: (sessionRes.data as any).status,
        createdAt: (sessionRes.data as any).created_at,
      };
      setSession(sessionData);

      // Fetch roll data
      const rollRes = await api.get(`/api/debate/${sessionId}/roll`);
      const rollData: DebateRoll = {
        id: rollRes.data.id,
        position: rollRes.data.position,
        themeModifier: rollRes.data.theme_modifier,
        mode: 'debate',
        players: rollRes.data.players,
      };
      setRoll(rollData);

      // If session is complete, fetch comparison
      if (sessionData.status === 'complete') {
        const compareRes = await api.get(
          `/api/debate/${sessionId}/compare`
        );
        const compareData: DebateComparison = {
          sessionId: compareRes.data.session_id,
          status: compareRes.data.status,
          roll: {
            id: compareRes.data.roll.id,
            position: compareRes.data.roll.position,
            themeModifier: compareRes.data.roll.theme_modifier,
          },
          creator: {
            userId: compareRes.data.creator.user_id,
            username: compareRes.data.creator.username,
            ranking: {
              id: compareRes.data.creator.ranking.id,
              rubric: compareRes.data.creator.ranking.rubric,
              playerOrder: compareRes.data.creator.ranking.player_order,
              kendallTauDistance:
                compareRes.data.creator.ranking.kendall_tau_distance,
              letterGrade: compareRes.data.creator.ranking.letter_grade,
            },
            consensusOrder: compareRes.data.creator.consensus_order,
          },
          opponent: {
            userId: compareRes.data.opponent.user_id,
            username: compareRes.data.opponent.username,
            ranking: {
              id: compareRes.data.opponent.ranking.id,
              rubric: compareRes.data.opponent.ranking.rubric,
              playerOrder: compareRes.data.opponent.ranking.player_order,
              kendallTauDistance:
                compareRes.data.opponent.ranking.kendall_tau_distance,
              letterGrade: compareRes.data.opponent.ranking.letter_grade,
            },
            consensusOrder: compareRes.data.opponent.consensus_order,
          },
          differences: compareRes.data.differences,
          playerNames: compareRes.data.player_names,
        };
        setComparison(compareData);
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as {
          response?: { status?: number; data?: { detail?: string } };
        };
        if (axiosErr.response?.status === 404) {
          setError('Debate session not found.');
        } else {
          setError(
            axiosErr.response?.data?.detail ||
              'Failed to load debate session.'
          );
        }
      } else {
        setError('Failed to load debate session.');
      }
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  const createSession = useCallback(async (): Promise<string | null> => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.post('/api/debate');
      return res.data.id;
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as {
          response?: { data?: { detail?: string } };
        };
        setError(
          axiosErr.response?.data?.detail ||
            'Failed to create debate session.'
        );
      } else {
        setError('Failed to create debate session.');
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const submitRanking = useCallback(
    async (
      playerOrder: number[],
      rubric: Rubric
    ): Promise<{ success: boolean; sessionStatus?: string }> => {
      if (!sessionId || !roll) {
        setError('No active debate session.');
        return { success: false };
      }

      setError(null);

      try {
        const res = await api.post(`/api/debate/${sessionId}/ranking`, {
          roll_id: roll.id,
          rubric,
          player_order: playerOrder,
        });
        setHasSubmitted(true);

        // If session is now complete, refetch to get comparison
        if (res.data.session_status === 'complete') {
          await fetchSession();
        }

        return {
          success: true,
          sessionStatus: res.data.session_status,
        };
      } catch (err: unknown) {
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosErr = err as {
            response?: { status?: number; data?: { detail?: string } };
          };
          if (axiosErr.response?.status === 409) {
            setHasSubmitted(true);
            setError('You have already submitted your ranking for this debate.');
          } else {
            setError(
              axiosErr.response?.data?.detail ||
                'Failed to submit ranking.'
            );
          }
        } else {
          setError('Failed to submit ranking.');
        }
        return { success: false };
      }
    },
    [sessionId, roll, fetchSession]
  );

  return {
    session,
    roll,
    comparison,
    loading,
    error,
    hasSubmitted,
    createSession,
    submitRanking,
    refetch: fetchSession,
  };
}
