import { useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useDebate } from '../hooks/useDebate';
import { DebateCreate, DebateCompare } from '../components/debate';
import type { Rubric } from '../types';

/**
 * Debate page — handles the full debate flow:
 * 1. If no sessionId, show the create debate UI
 * 2. If session is waiting and user hasn't submitted, show ranking UI
 * 3. If session is waiting and user has submitted, show waiting state
 * 4. If session is complete, show comparison view
 */
export function Debate() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const {
    session,
    roll,
    comparison,
    loading,
    error,
    hasSubmitted,
    submitRanking,
    refetch,
  } = useDebate(sessionId);

  const [rubric, setRubric] = useState<Rubric>('analytics');
  const [playerOrder, setPlayerOrder] = useState<number[]>([]);
  const [rubricLocked, setRubricLocked] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Initialize player order from roll when it loads
  const initializeOrder = useCallback(() => {
    if (roll && playerOrder.length === 0) {
      setPlayerOrder(roll.players.map((p) => p.id));
    }
  }, [roll, playerOrder.length]);

  // Call initialize when roll is available
  if (roll && playerOrder.length === 0) {
    initializeOrder();
  }

  // Handle player reorder (simple swap for demo — real UI would use @dnd-kit)
  const handleMoveUp = (index: number) => {
    if (index <= 0) return;
    if (!rubricLocked) setRubricLocked(true);
    const newOrder = [...playerOrder];
    [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
    setPlayerOrder(newOrder);
  };

  const handleMoveDown = (index: number) => {
    if (index >= playerOrder.length - 1) return;
    if (!rubricLocked) setRubricLocked(true);
    const newOrder = [...playerOrder];
    [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
    setPlayerOrder(newOrder);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    await submitRanking(playerOrder, rubric);
    setSubmitting(false);
  };

  // No sessionId — show create UI
  if (!sessionId) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <DebateCreate />
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <p className="text-gray-400">Loading debate...</p>
      </div>
    );
  }

  // Error state
  if (error && !session) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4" role="alert">{error}</p>
          <button
            onClick={refetch}
            className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Session is complete — show comparison
  if (session?.status === 'complete' && comparison) {
    return (
      <div className="min-h-screen bg-gray-900 py-8 px-4">
        <div className="max-w-2xl mx-auto">
          <DebateCompare comparison={comparison} />
        </div>
      </div>
    );
  }

  // User has submitted, waiting for opponent
  if (hasSubmitted || (session?.status === 'waiting' && !roll)) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-bold text-white mb-2">
            Ranking Submitted!
          </h2>
          <p className="text-gray-400 mb-4">
            Waiting for your opponent to submit their ranking...
          </p>
          <button
            onClick={refetch}
            className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
          >
            Check Status
          </button>
          {error && (
            <p className="text-red-400 text-sm mt-2" role="alert">{error}</p>
          )}
        </div>
      </div>
    );
  }

  // Active ranking phase
  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-lg mx-auto">
        {/* Roll display */}
        {roll && (
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-white">Debate Mode</h2>
            <div className="flex justify-center gap-2 mt-2">
              <span className="px-3 py-1 bg-blue-900/50 text-blue-300 rounded-full text-sm">
                {roll.position}
              </span>
              <span className="px-3 py-1 bg-purple-900/50 text-purple-300 rounded-full text-sm">
                {roll.themeModifier}
              </span>
            </div>
          </div>
        )}

        {/* Rubric selector */}
        <div className="mb-6">
          <p className="text-sm text-gray-400 mb-2 text-center">
            Choose your scoring rubric:
          </p>
          <div className="flex justify-center gap-3">
            <button
              onClick={() => !rubricLocked && setRubric('analytics')}
              disabled={rubricLocked}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                rubric === 'analytics'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              } ${rubricLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
              aria-pressed={rubric === 'analytics'}
            >
              Analytics
            </button>
            <button
              onClick={() => !rubricLocked && setRubric('reputation')}
              disabled={rubricLocked}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                rubric === 'reputation'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              } ${rubricLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
              aria-pressed={rubric === 'reputation'}
            >
              Reputation
            </button>
          </div>
          {rubricLocked && (
            <p className="text-xs text-gray-500 text-center mt-1">
              Rubric locked after first reorder
            </p>
          )}
        </div>

        {/* Player ranking list */}
        <div className="space-y-2 mb-6">
          {playerOrder.map((playerId, idx) => {
            const player = roll?.players.find((p) => p.id === playerId);
            return (
              <div
                key={playerId}
                className="flex items-center gap-3 bg-gray-800 rounded-lg p-3"
              >
                <span className="text-gray-500 font-mono text-sm w-6 text-center">
                  {idx + 1}
                </span>
                <div className="flex-1">
                  <p className="text-white text-sm font-medium">
                    {player?.name || `Player ${playerId}`}
                  </p>
                  <p className="text-gray-500 text-xs">
                    {player?.position} · {player?.era}
                  </p>
                </div>
                <div className="flex flex-col gap-1">
                  <button
                    onClick={() => handleMoveUp(idx)}
                    disabled={idx === 0}
                    className="text-gray-400 hover:text-white disabled:opacity-30 text-xs"
                    aria-label={`Move ${player?.name || 'player'} up`}
                  >
                    ▲
                  </button>
                  <button
                    onClick={() => handleMoveDown(idx)}
                    disabled={idx === playerOrder.length - 1}
                    className="text-gray-400 hover:text-white disabled:opacity-30 text-xs"
                    aria-label={`Move ${player?.name || 'player'} down`}
                  >
                    ▼
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={!rubricLocked || submitting}
          className="w-full py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-600 
                     disabled:cursor-not-allowed text-white font-semibold rounded-lg 
                     transition-colors"
          aria-label="Submit ranking"
        >
          {submitting ? 'Submitting...' : 'Lock In My Ranking'}
        </button>

        {error && (
          <p className="text-red-400 text-sm text-center mt-3" role="alert">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
