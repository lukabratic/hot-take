import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';
import { BlindRankingBoard } from '../components/ranking/BlindRankingBoard';
import { RubricSelector } from '../components/ranking/RubricSelector';
import { RollDisplay } from '../components/common/RollDisplay';
import { CategorySelector } from '../components/category/CategorySelector';
import api from '../services/api';
import type { Player, Roll, Rubric, GameMode, ThemeModifier, CategoryType } from '../types';

/** API response for HoopIQ mode — players have stats only, no names. */
interface HoopIQRollResponse {
  id: number;
  position: string;
  theme_modifier: string;
  mode: 'hoopiq';
  players: Array<{
    id: number;
    career_stats: Record<string, number>;
    peak_stats: Record<string, number>;
    playoff_stats: Record<string, number> | null;
    all_nba_selections: number;
    all_star_selections: number;
    championships: number;
    mvp_vote_shares: number;
  }>;
}

type Phase = 'category' | 'rubric' | 'blind';

/**
 * Play page at /play/:mode
 *
 * Two phases:
 * 1. Rubric selection — pick Analytics or Reputation
 * 2. Blind ranking — players revealed one at a time, place each immediately.
 *    Once all placed, auto-submits. No review, no going back.
 */
export function Play() {
  const { mode } = useParams<{ mode: string }>();
  const navigate = useNavigate();
  const { isSignedIn, getToken } = useAuth();

  const [roll, setRoll] = useState<Roll | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [rubric, setRubric] = useState<Rubric | null>(null);
  // Daily mode skips category selection; quickplay and hoopiq start at category phase
  const [phase, setPhase] = useState<Phase>(mode === 'daily' ? 'rubric' : 'category');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedCategoryType, setSelectedCategoryType] = useState<CategoryType | null>(null);
  const [selectedCategoryValue, setSelectedCategoryValue] = useState<string | null>(null);
  const retryCount = useRef(0);

  // Fetch Roll — for daily mode on mount, for quickplay/hoopiq after category selection
  useEffect(() => {
    // For quickplay and hoopiq, defer fetch until category is selected
    if (mode !== 'daily' && !selectedCategoryValue) {
      setLoading(false);
      return;
    }

    async function fetchRoll() {
      setLoading(true);
      setError(null);
      try {
        if (mode === 'hoopiq') {
          const params = selectedCategoryType && selectedCategoryValue
            ? { category_type: selectedCategoryType, category_value: selectedCategoryValue }
            : undefined;
          const response = await api.get<HoopIQRollResponse>('/api/hoopiq', { params });
          const data = response.data;
          const mappedRoll: Roll = {
            id: data.id,
            position: data.position as Roll['position'],
            themeModifier: data.theme_modifier as ThemeModifier,
            dailyDate: null,
            mode: 'hoopiq',
            players: data.players.map((p) => ({
              id: p.id,
              name: '???',
              position: '',
              era: '',
              careerStats: p.career_stats as unknown as Player['careerStats'],
              peakStats: p.peak_stats as unknown as Player['peakStats'],
              playoffStats: p.playoff_stats as unknown as Player['playoffStats'],
              allNbaSelections: p.all_nba_selections ?? 0,
              mvpVoteShares: p.mvp_vote_shares ?? 0,
              championships: p.championships ?? 0,
              allStarSelections: p.all_star_selections ?? 0,
              hofRank: null,
              bbrefId: '',
            })),
            categoryType: selectedCategoryType ?? undefined,
            categoryValue: selectedCategoryValue ?? undefined,
          };
          setRoll(mappedRoll);
        } else {
          const gameMode: GameMode = mode === 'daily' ? 'daily' : 'quickplay';
          const endpoint = gameMode === 'daily' ? '/api/daily' : '/api/quickplay';
          const params = gameMode === 'quickplay' && selectedCategoryType && selectedCategoryValue
            ? { category_type: selectedCategoryType, category_value: selectedCategoryValue }
            : undefined;
          const response = await api.get<Roll>(endpoint, { params });
          setRoll(response.data);
        }
      } catch (err: unknown) {
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosErr = err as { response?: { status?: number; headers?: Record<string, string>; data?: { detail?: string | { message: string; ranking_id: number } } } };
          if (axiosErr.response?.status === 401 && isSignedIn && retryCount.current < 2) {
            retryCount.current += 1;
            await new Promise((r) => setTimeout(r, 1000));
            await getToken({ skipCache: true });
            return fetchRoll();
          } else if (axiosErr.response?.status === 409) {
            // Already submitted — redirect to reveal
            const detail = axiosErr.response?.data?.detail;
            const rankingId = typeof detail === 'object' && detail ? detail.ranking_id : null;
            if (rankingId) {
              navigate(`/reveal/${rankingId}`, { replace: true });
            } else {
              setError("You already completed today's challenge!");
            }
          } else if (axiosErr.response?.status === 401) {
            setError('Failed to load challenge. Please try again.');
          } else {
            setError('Failed to load challenge. Please try again.');
          }
        } else {
          setError('Failed to load challenge. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    }

    retryCount.current = 0;
    fetchRoll();
  }, [mode, isSignedIn, getToken, navigate, selectedCategoryType, selectedCategoryValue]);

  // Handle category selection — store selection and move to rubric phase
  const handleCategorySelect = useCallback((type: CategoryType, value: string) => {
    setSelectedCategoryType(type);
    setSelectedCategoryValue(value);
    setPhase('rubric');
  }, []);

  // Handle rubric selection — move to blind phase
  const handleRubricSelect = useCallback((r: Rubric) => {
    setRubric(r);
    setPhase('blind');
  }, []);

  // Handle blind ranking complete — auto-submit immediately
  const handleBlindComplete = useCallback(async (players: Player[]) => {
    if (!roll || !rubric) return;

    setIsSubmitting(true);
    try {
      const response = await api.post<{ id: number }>('/api/rankings', {
        roll_id: roll.id,
        player_order: players.map((p) => p.id),
        rubric,
      });
      navigate(`/reveal/${response.data.id}`);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string | unknown[] } } };
        if (axiosErr.response?.status === 409) {
          setError('You already submitted a ranking for this challenge.');
        } else {
          const detail = axiosErr.response?.data?.detail;
          const message =
            typeof detail === 'string' ? detail : 'Submission failed. Please try again.';
          setError(message);
        }
      } else {
        setError('Submission failed. Please try again.');
      }
      setIsSubmitting(false);
    }
  }, [roll, rubric, navigate]);

  // --- Render states ---

  // Show category selector before roll is fetched (quickplay/hoopiq only)
  if (phase === 'category') {
    return (
      <div className="min-h-screen flex flex-col items-center p-4 pb-8">
        <div className="w-full max-w-md space-y-6">
          <header className="text-center space-y-3 pt-4">
            <h1 className="text-2xl font-bold text-white">
              {mode === 'hoopiq' ? 'HoopIQ Challenge' : 'Quick Play'}
            </h1>
            <p className="text-gray-400 text-sm">Choose your category</p>
          </header>
          <CategorySelector onCategorySelect={handleCategorySelect} />
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-nba-gold border-t-transparent rounded-full mx-auto" />
          <p className="text-gray-400 mt-4">Loading challenge…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <p className="text-red-400 text-lg">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!roll) return null;

  return (
    <div className="min-h-screen flex flex-col items-center p-4 pb-8">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <header className="text-center space-y-3 pt-4">
          <h1 className="text-2xl font-bold text-white">
            {mode === 'daily'
              ? "Today's Challenge"
              : mode === 'hoopiq'
              ? 'HoopIQ Challenge'
              : 'Quick Play'}
          </h1>
          <RollDisplay position={roll.position} themeModifier={roll.themeModifier} />
        </header>

        {/* Phase 1: Rubric Selection */}
        {phase === 'rubric' && (
          <div className="space-y-4">
            <RubricSelector
              selected={null}
              onSelect={handleRubricSelect}
              locked={false}
            />
            <p className="text-sm text-gray-400 text-center">
              Pick your rubric to start. Players will be revealed one at a time.
            </p>
          </div>
        )}

        {/* Phase 2: Blind Ranking */}
        {phase === 'blind' && roll.players && (
          <div className="space-y-4">
            <div className="text-center">
              <span className="inline-block px-3 py-1 rounded-full bg-gray-700 text-gray-300 text-xs">
                Scoring: {rubric === 'analytics' ? 'Analytics' : 'Reputation'}
              </span>
            </div>
            {isSubmitting ? (
              <div className="text-center py-8">
                <div className="animate-spin h-8 w-8 border-4 border-nba-gold border-t-transparent rounded-full mx-auto" />
                <p className="text-gray-400 mt-4">Submitting your ranking…</p>
              </div>
            ) : (
              <BlindRankingBoard
                players={roll.players}
                onComplete={handleBlindComplete}
                variant={mode === 'hoopiq' ? 'hoopiq' : 'default'}
                themeModifier={roll.themeModifier}
                rubric={rubric}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
