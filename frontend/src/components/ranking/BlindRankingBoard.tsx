import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Player, Rubric, ThemeModifier } from '../../types';

interface BlindRankingBoardProps {
  players: Player[];
  onComplete: (rankedPlayers: Player[]) => void;
  variant?: 'default' | 'hoopiq';
  themeModifier?: ThemeModifier;
  rubric?: Rubric | null;
}

/**
 * Blind ranking interface: players are revealed one at a time.
 * For each new player, the user picks a slot (position) in the current ranking.
 * Once placed, the next player is revealed. No going back.
 */
export function BlindRankingBoard({
  players,
  onComplete,
  variant = 'default',
  rubric,
}: BlindRankingBoardProps) {
  const [ranked, setRanked] = useState<Player[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const currentPlayer = players[currentIndex] ?? null;
  const isComplete = currentIndex >= players.length;

  const handleInsert = useCallback(
    (position: number) => {
      if (!currentPlayer) return;

      const newRanked = [...ranked];
      newRanked.splice(position, 0, currentPlayer);
      setRanked(newRanked);

      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);

      if (nextIndex >= players.length) {
        onComplete(newRanked);
      }
    },
    [currentPlayer, ranked, currentIndex, players.length, onComplete]
  );

  if (isComplete) {
    return null; // Parent handles the completed state
  }

  return (
    <div className="space-y-4">
      {/* Progress indicator */}
      <div className="flex items-center justify-between text-sm text-gray-400">
        <span>
          Player {currentIndex + 1} of {players.length}
        </span>
        <div className="flex gap-1">
          {players.map((_, i) => (
            <div
              key={i}
              className={`w-2 h-2 rounded-full ${
                i < currentIndex
                  ? 'bg-nba-gold'
                  : i === currentIndex
                  ? 'bg-white'
                  : 'bg-gray-600'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Current player reveal */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentPlayer.id}
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: -20 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          className="p-5 rounded-xl border-2 border-nba-gold bg-gray-800/80 text-center"
        >
          {variant === 'hoopiq' ? (
            <div className="space-y-1">
              <p className="text-nba-gold font-bold text-lg">Mystery Player</p>
              <p className="text-gray-300 text-sm">
                {currentPlayer.careerStats?.pts ?? 0} PPG ·{' '}
                {currentPlayer.careerStats?.reb ?? 0} RPG ·{' '}
                {currentPlayer.careerStats?.ast ?? 0} APG
              </p>
              <p className="text-gray-500 text-xs">
                {currentPlayer.allNbaSelections}× All-NBA · {currentPlayer.allStarSelections}× All-Star · {currentPlayer.championships}× Champ
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <div
                className="mx-auto w-14 h-14 rounded-full bg-gray-600
                           flex items-center justify-center text-lg font-bold text-gray-200"
              >
                {currentPlayer.name
                  .split(' ')
                  .map((n) => n[0])
                  .join('')}
              </div>
              <p className="text-white font-bold text-xl">
                {currentPlayer.name}
              </p>
              <p className="text-gray-400 text-sm">
                {currentPlayer.position} · {currentPlayer.era}
                {(currentPlayer as any).team && ` · ${(currentPlayer as any).team}`}
              </p>
              {/* Basic stats based on rubric */}
              {rubric === 'analytics' && currentPlayer.careerStats && (
                <p className="text-gray-500 text-xs">
                  {currentPlayer.careerStats.pts} PPG · {currentPlayer.careerStats.reb} RPG · {currentPlayer.careerStats.ast} APG · PER {currentPlayer.careerStats.per}
                </p>
              )}
              {rubric === 'reputation' && (
                <p className="text-gray-500 text-xs">
                  {currentPlayer.allNbaSelections}× All-NBA · {currentPlayer.allStarSelections}× All-Star · {currentPlayer.championships}× Champ
                </p>
              )}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Instruction */}
      <p className="text-center text-gray-400 text-sm">
        {ranked.length === 0
          ? 'Tap below to place this player as #1'
          : 'Where does this player rank?'}
      </p>

      {/* Insert slots */}
      <div className="space-y-1">
        {ranked.length === 0 ? (
          <button
            onClick={() => handleInsert(0)}
            className="w-full py-3 rounded-lg border-2 border-dashed border-nba-gold/50
                       text-nba-gold font-semibold hover:border-nba-gold hover:bg-nba-gold/10
                       transition-all"
          >
            Place as #1
          </button>
        ) : (
          <>
            {/* Insert before first */}
            <InsertSlot
              label={`#1 — above ${ranked[0].name}`}
              onClick={() => handleInsert(0)}
            />

            {ranked.map((player, idx) => (
              <div key={player.id}>
                {/* The placed player */}
                <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/50 border border-gray-700">
                  <span className="w-7 h-7 flex items-center justify-center rounded-full bg-nba-blue text-white font-bold text-xs">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <span className="text-white font-medium text-sm truncate block">
                      {variant === 'hoopiq' ? `Player ${idx + 1}` : player.name}
                    </span>
                    {variant === 'hoopiq' && (
                      <span className="text-gray-500 text-xs">
                        {player.careerStats?.pts ?? 0} PPG · {player.careerStats?.reb ?? 0} RPG · {player.careerStats?.ast ?? 0} APG · {player.allNbaSelections}× All-NBA · {player.allStarSelections}× AS
                      </span>
                    )}
                  </div>
                </div>

                {/* Insert after this player */}
                <InsertSlot
                  label={`#${idx + 2} — below ${variant === 'hoopiq' ? `Player ${idx + 1}` : player.name}`}
                  onClick={() => handleInsert(idx + 1)}
                />
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function InsertSlot({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full py-2 my-1 rounded-md border border-dashed border-gray-600
                 text-gray-400 text-sm hover:border-nba-gold hover:text-nba-gold
                 hover:bg-nba-gold/5 transition-all"
    >
      {label}
    </button>
  );
}
