import type { DebateComparison } from '../../types';

interface DebateCompareProps {
  comparison: DebateComparison;
}

/**
 * DebateCompare component — displays both participants' rankings side by side
 * with differences highlighted. Shows letter grades, Kendall tau distances,
 * and which slots the two users disagree on.
 */
export function DebateCompare({ comparison }: DebateCompareProps) {
  const { creator, opponent, differences, playerNames, roll } = comparison;

  const gradeColor = (grade: string): string => {
    switch (grade) {
      case 'S':
        return 'text-yellow-400';
      case 'A':
        return 'text-green-400';
      case 'B':
        return 'text-blue-400';
      case 'C':
        return 'text-orange-400';
      case 'D':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="flex flex-col gap-6 p-4">
      {/* Roll info header */}
      <div className="text-center">
        <h2 className="text-xl font-bold text-white">Debate Results</h2>
        <p className="text-gray-400 mt-1">
          {roll.position} · {roll.themeModifier}
        </p>
      </div>

      {/* Score summary */}
      <div className="flex justify-center gap-8">
        <div className="text-center">
          <p className="text-sm text-gray-400">{creator.username}</p>
          <p
            className={`text-3xl font-bold ${gradeColor(creator.ranking.letterGrade)}`}
          >
            {creator.ranking.letterGrade}
          </p>
          <p className="text-xs text-gray-500">
            {creator.ranking.kendallTauDistance} swap
            {creator.ranking.kendallTauDistance !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center text-gray-600 text-2xl font-bold">
          vs
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-400">{opponent.username}</p>
          <p
            className={`text-3xl font-bold ${gradeColor(opponent.ranking.letterGrade)}`}
          >
            {opponent.ranking.letterGrade}
          </p>
          <p className="text-xs text-gray-500">
            {opponent.ranking.kendallTauDistance} swap
            {opponent.ranking.kendallTauDistance !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Side-by-side rankings */}
      <div className="grid grid-cols-[1fr_auto_1fr] gap-2 items-start">
        {/* Column headers */}
        <p className="text-sm font-medium text-gray-400 text-center pb-2">
          {creator.username}
        </p>
        <p className="text-sm font-medium text-gray-500 text-center pb-2">
          #
        </p>
        <p className="text-sm font-medium text-gray-400 text-center pb-2">
          {opponent.username}
        </p>

        {/* Ranking rows */}
        {creator.ranking.playerOrder.map((playerId, idx) => {
          const slot = idx + 1;
          const isDifferent = differences.includes(slot);
          const opponentPlayerId = opponent.ranking.playerOrder[idx];

          return (
            <div key={slot} className="contents">
              {/* Creator's pick */}
              <div
                className={`rounded-lg px-3 py-2 text-sm text-center ${
                  isDifferent
                    ? 'bg-orange-900/30 border border-orange-500/50'
                    : 'bg-gray-800'
                }`}
              >
                <span className="text-white">
                  {playerNames[playerId] || `Player ${playerId}`}
                </span>
              </div>

              {/* Slot number */}
              <div className="flex items-center justify-center">
                <span className="text-gray-500 text-xs font-mono w-6 text-center">
                  {slot}
                </span>
              </div>

              {/* Opponent's pick */}
              <div
                className={`rounded-lg px-3 py-2 text-sm text-center ${
                  isDifferent
                    ? 'bg-orange-900/30 border border-orange-500/50'
                    : 'bg-gray-800'
                }`}
              >
                <span className="text-white">
                  {playerNames[opponentPlayerId] || `Player ${opponentPlayerId}`}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Differences summary */}
      {differences.length > 0 ? (
        <p className="text-center text-sm text-gray-400">
          You disagreed on{' '}
          <span className="text-orange-400 font-medium">
            {differences.length}
          </span>{' '}
          slot{differences.length !== 1 ? 's' : ''} — time to debate!
        </p>
      ) : (
        <p className="text-center text-sm text-green-400">
          You both ranked them the same. Great minds think alike!
        </p>
      )}

      {/* Rubric info */}
      <div className="flex justify-center gap-6 text-xs text-gray-500">
        <span>
          {creator.username}: {creator.ranking.rubric} rubric
        </span>
        <span>
          {opponent.username}: {opponent.ranking.rubric} rubric
        </span>
      </div>
    </div>
  );
}
