import type { Rubric } from '../../types';

interface RubricSelectorProps {
  selected: Rubric | null;
  onSelect: (rubric: Rubric) => void;
  /** Whether selection is locked (after first drag operation) */
  locked: boolean;
}

const RUBRIC_INFO: Record<Rubric, { label: string; description: string }> = {
  analytics: {
    label: 'Analytics',
    description: 'Scored by era-adjusted VORP, BPM, Win Shares, and PER',
  },
  reputation: {
    label: 'Reputation',
    description: 'Scored by All-NBA, MVP shares, HOF rank, and All-Star selections',
  },
};

/**
 * Toggle selector for choosing Analytics vs Reputation rubric.
 * Locks after the first drag operation so users cannot change mid-ranking.
 */
export function RubricSelector({ selected, onSelect, locked }: RubricSelectorProps) {
  return (
    <div className="w-full" role="radiogroup" aria-label="Scoring rubric">
      <p className="text-sm text-gray-400 mb-2 font-medium">
        Choose your scoring rubric
        {locked && (
          <span className="ml-2 text-xs text-nba-gold">(locked)</span>
        )}
      </p>
      <div className="grid grid-cols-2 gap-3">
        {(Object.entries(RUBRIC_INFO) as [Rubric, typeof RUBRIC_INFO['analytics']][]).map(
          ([rubric, info]) => {
            const isSelected = selected === rubric;
            return (
              <button
                key={rubric}
                type="button"
                role="radio"
                aria-checked={isSelected}
                disabled={locked && !isSelected}
                onClick={() => onSelect(rubric)}
                className={`
                  p-3 rounded-lg border text-left transition-all
                  ${isSelected
                    ? 'border-nba-gold bg-nba-gold/10 text-white'
                    : 'border-gray-700 bg-gray-800 text-gray-300 hover:border-gray-500'
                  }
                  ${locked && !isSelected ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <p className="font-semibold text-sm">{info.label}</p>
                <p className="text-xs text-gray-400 mt-1">{info.description}</p>
              </button>
            );
          }
        )}
      </div>
    </div>
  );
}
