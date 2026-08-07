import type { CategoryValue } from '../../types';

interface PickGridProps {
  /** Available category values to display */
  values: CategoryValue[];
  /** Called when a value is selected */
  onSelect: (value: string) => void;
  /** Whether interactions are disabled (e.g. during spin) */
  disabled?: boolean;
}

/**
 * PickGrid — a grid of tappable tiles for manual category selection.
 * Values with fewer than 5 players are shown as disabled (grayed, non-interactive).
 */
export function PickGrid({ values, onSelect, disabled = false }: PickGridProps) {
  return (
    <div
      className="grid grid-cols-2 sm:grid-cols-3 gap-3"
      role="listbox"
      aria-label="Category selection grid"
    >
      {values.map((item) => {
        const isDisabled = item.disabled || disabled;

        return (
          <button
            key={item.value}
            onClick={() => !isDisabled && onSelect(item.value)}
            disabled={isDisabled}
            role="option"
            aria-selected={false}
            aria-disabled={isDisabled}
            className={`flex flex-col items-center justify-center p-4 rounded-lg border transition-all ${
              isDisabled
                ? 'bg-gray-800/50 border-gray-700 text-gray-600 cursor-not-allowed opacity-50'
                : 'bg-gray-800 border-gray-600 text-white hover:border-nba-gold hover:bg-gray-700 active:scale-95 cursor-pointer'
            }`}
          >
            <span className="text-sm font-semibold text-center leading-tight">
              {item.label}
            </span>
            {item.playerCount > 0 && (
              <span
                className={`text-xs mt-1 ${isDisabled ? 'text-gray-600' : 'text-gray-400'}`}
              >
                {item.playerCount} player{item.playerCount !== 1 ? 's' : ''}
              </span>
            )}
            {item.disabled && (
              <span className="text-xs text-red-400/70 mt-0.5">Unavailable</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
