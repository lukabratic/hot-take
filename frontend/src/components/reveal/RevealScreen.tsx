import { motion } from 'framer-motion';
import type { GameMode, Player, Position, RevealResult, ThemeModifier } from '../../types';
import { LetterGradeBadge } from '../common/LetterGradeBadge';
import { ShareButton } from '../share/ShareButton';
import { ComparisonView } from './ComparisonView';
import { HoopIQComparisonView } from './HoopIQComparisonView';
import { CommunityHeatmap } from './CommunityHeatmap';
import { ControversialPick } from './ControversialPick';

interface RevealScreenProps {
  /** Full reveal result from the API */
  result: RevealResult;
  /** Players associated with this Roll, keyed by ID */
  playersById: Record<number, Player>;
  /** Roll position for the share card */
  position?: Position;
  /** Roll theme modifier for the share card */
  themeModifier?: ThemeModifier;
  /** Game mode — when "hoopiq", renders HoopIQ name-reveal comparison */
  mode?: GameMode;
}

/**
 * The post-round results screen showing the user's ranking vs consensus,
 * community heatmap, controversial pick callout, score, commentary, and share button.
 */
export function RevealScreen({ result, playersById, position, themeModifier, mode }: RevealScreenProps) {
  const { ranking, consensusOrder, communityHeatmap, controversialPick, commentary } = result;

  return (
    <div className="w-full max-w-md mx-auto space-y-8 py-4">
      {/* Grade Badge + Commentary */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center gap-3"
      >
        <LetterGradeBadge
          grade={ranking.letterGrade}
          distance={ranking.kendallTauDistance}
        />

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="text-gray-300 text-center text-sm italic"
        >
          {commentary}
        </motion.p>
      </motion.div>

      {/* Side-by-side Comparison */}
      {mode === 'hoopiq' ? (
        <HoopIQComparisonView
          playersById={playersById}
          userOrder={ranking.playerOrder}
          consensusOrder={consensusOrder}
          themeModifier={themeModifier}
        />
      ) : (
        <ComparisonView
          playersById={playersById}
          userOrder={ranking.playerOrder}
          consensusOrder={consensusOrder}
        />
      )}

      {/* Community Heatmap */}
      <CommunityHeatmap
        heatmap={communityHeatmap}
        playersById={playersById}
        userOrder={ranking.playerOrder}
      />

      {/* Controversial Pick */}
      {controversialPick && (
        <ControversialPick
          pick={controversialPick}
          playersById={playersById}
        />
      )}

      {/* Rubric indicator badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.8 }}
        className="flex justify-center"
      >
        <div
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border ${
            ranking.rubric === 'analytics'
              ? 'bg-blue-900/40 border-blue-500/50 text-blue-300'
              : 'bg-amber-900/40 border-amber-500/50 text-amber-300'
          }`}
          aria-label={`Scored using the ${ranking.rubric} rubric`}
        >
          <span aria-hidden="true">
            {ranking.rubric === 'analytics' ? '📊' : '🏆'}
          </span>
          <span>
            {ranking.rubric === 'analytics' ? 'Analytics' : 'Reputation'} Consensus
          </span>
        </div>
      </motion.div>

      {/* Share button */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="flex justify-center w-full"
      >
        {position && themeModifier ? (
          <ShareButton
            ranking={ranking}
            playersById={playersById}
            position={position}
            themeModifier={themeModifier}
          />
        ) : (
          <button
            className="px-6 py-3 rounded-full bg-nba-gold text-gray-900 font-bold
                       hover:bg-yellow-400 transition-colors shadow-lg shadow-nba-gold/20"
            aria-label="Share your result"
            onClick={() => {
              // Fallback: copy text to clipboard
              const text = `🔥 HOT TAKE — Grade: ${ranking.letterGrade} (${ranking.kendallTauDistance} swaps)`;
              navigator.clipboard.writeText(text).catch(() => {});
            }}
          >
            Share Result 🔗
          </button>
        )}
      </motion.div>
    </div>
  );
}
