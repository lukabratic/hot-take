import type { Position, ThemeModifier } from '../../types';

interface RollDisplayProps {
  position: Position;
  themeModifier: ThemeModifier;
}

/**
 * Displays the Roll's Position and Theme Modifier as styled badges.
 */
export function RollDisplay({ position, themeModifier }: RollDisplayProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3">
      {/* Position badge */}
      <span
        className="inline-flex items-center px-3 py-1.5 rounded-full
                   bg-nba-blue/80 text-white font-semibold text-sm border border-nba-blue"
      >
        {position}
      </span>

      {/* Theme modifier badge */}
      <span
        className="inline-flex items-center px-3 py-1.5 rounded-full
                   bg-gray-700/80 text-gray-200 font-medium text-sm border border-gray-600"
      >
        {themeModifier}
      </span>
    </div>
  );
}
