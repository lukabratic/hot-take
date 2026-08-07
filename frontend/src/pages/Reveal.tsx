import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { RevealScreen } from '../components/reveal/RevealScreen';
import api from '../services/api';
import type { Player, Position, RevealResult, ThemeModifier } from '../types';

/** API response uses snake_case; this maps to our frontend types. */
interface ApiRevealResponse {
  ranking: {
    id: number;
    user_id: string;
    roll_id: number;
    rubric: 'analytics' | 'reputation';
    player_order: number[];
    kendall_tau_distance: number;
    letter_grade: 'S' | 'A' | 'B' | 'C' | 'D';
    mode: 'daily' | 'quickplay' | 'hoopiq' | 'debate';
    created_at: string;
  };
  consensus_order: number[];
  community_heatmap: {
    data: Record<string, Record<string, number>>;
    total_submissions: number;
  };
  controversial_pick: {
    player_id: number;
    slot: number;
    community_agreement: number;
  } | null;
  commentary: string;
}

/** API response for a roll with players. */
interface ApiRollResponse {
  id: number;
  position: string;
  theme_modifier: string;
  daily_date: string | null;
  mode: string;
  players: Array<{
    id: number;
    name: string;
    position: string;
    era: string | null;
    career_stats: Record<string, number>;
    peak_stats: Record<string, number>;
    playoff_stats: Record<string, number> | null;
    all_nba_selections: number;
    mvp_vote_shares: number;
    championships: number;
    all_star_selections: number;
    hof_rank: number | null;
    bbref_id: string;
  }>;
}

/** Transform API heatmap response to frontend type (string keys → number keys). */
function transformHeatmap(apiData: Record<string, Record<string, number>>) {
  const result: Record<number, Record<number, number>> = {};
  for (const [playerId, slots] of Object.entries(apiData)) {
    result[Number(playerId)] = {};
    for (const [slot, pct] of Object.entries(slots)) {
      result[Number(playerId)][Number(slot)] = pct;
    }
  }
  return result;
}

/**
 * Reveal page at /reveal/:rankingId
 * Fetches the ranking result and associated roll/player data,
 * then renders the full RevealScreen composition.
 */
export function Reveal() {
  const { rankingId } = useParams<{ rankingId: string }>();

  const [revealResult, setRevealResult] = useState<RevealResult | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [rollPosition, setRollPosition] = useState<Position | undefined>();
  const [rollThemeModifier, setRollThemeModifier] = useState<ThemeModifier | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchReveal() {
      if (!rankingId) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch the reveal data
        const revealRes = await api.get<ApiRevealResponse>(`/api/rankings/${rankingId}`);
        const data = revealRes.data;

        // Transform to frontend types
        const transformed: RevealResult = {
          ranking: {
            id: data.ranking.id,
            userId: data.ranking.user_id,
            rollId: data.ranking.roll_id,
            rubric: data.ranking.rubric,
            playerOrder: data.ranking.player_order,
            kendallTauDistance: data.ranking.kendall_tau_distance,
            letterGrade: data.ranking.letter_grade,
            mode: data.ranking.mode,
            createdAt: data.ranking.created_at,
          },
          consensusOrder: data.consensus_order,
          communityHeatmap: {
            data: transformHeatmap(data.community_heatmap.data),
            totalSubmissions: data.community_heatmap.total_submissions,
          },
          controversialPick: data.controversial_pick
            ? {
                playerId: data.controversial_pick.player_id,
                slot: data.controversial_pick.slot,
                communityAgreement: data.controversial_pick.community_agreement,
              }
            : null,
          commentary: data.commentary,
        };

        setRevealResult(transformed);

        // Fetch the roll to get player details
        const rollRes = await api.get<ApiRollResponse>(
          `/api/rolls/${data.ranking.roll_id}`
        );
        setRollPosition(rollRes.data.position as Position);
        setRollThemeModifier(rollRes.data.theme_modifier as ThemeModifier);
        setPlayers(
          rollRes.data.players.map((p) => ({
            id: p.id,
            name: p.name,
            position: p.position,
            era: p.era ?? '',
            careerStats: p.career_stats as unknown as Player['careerStats'],
            peakStats: p.peak_stats as unknown as Player['peakStats'],
            playoffStats: p.playoff_stats as unknown as Player['playoffStats'],
            allNbaSelections: p.all_nba_selections,
            mvpVoteShares: p.mvp_vote_shares,
            championships: p.championships,
            allStarSelections: p.all_star_selections,
            hofRank: p.hof_rank,
            bbrefId: p.bbref_id,
          }))
        );
      } catch (err: unknown) {
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosErr = err as { response?: { status?: number } };
          if (axiosErr.response?.status === 404) {
            setError('Ranking not found. It may have been removed.');
          } else {
            setError('Failed to load results. Please try again.');
          }
        } else {
          setError('Failed to load results. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    }

    fetchReveal();
  }, [rankingId]);

  // Build playersById lookup
  const playersById = useMemo(() => {
    const map: Record<number, Player> = {};
    for (const p of players) {
      map[p.id] = p;
    }
    return map;
  }, [players]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-nba-gold border-t-transparent rounded-full mx-auto" />
          <p className="text-gray-400 mt-4">Loading results…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <p className="text-red-400 text-lg">{error}</p>
          <Link
            to="/"
            className="inline-block mt-4 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
          >
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  if (!revealResult) return null;

  return (
    <div className="min-h-screen flex flex-col items-center p-4 pb-8">
      {/* Header */}
      <header className="text-center pt-4 pb-2">
        <h1 className="text-2xl font-bold text-white">Your Results</h1>
      </header>

      <RevealScreen result={revealResult} playersById={playersById} position={rollPosition} themeModifier={rollThemeModifier} mode={revealResult.ranking.mode} />

      {/* Play again CTA */}
      <div className="mt-8 flex gap-3">
        <Link
          to="/play/quickplay"
          className="px-4 py-2 rounded-lg bg-gray-700 text-white hover:bg-gray-600 text-sm font-medium"
        >
          Play Again
        </Link>
        <Link
          to="/"
          className="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 text-sm font-medium"
        >
          Home
        </Link>
      </div>
    </div>
  );
}
