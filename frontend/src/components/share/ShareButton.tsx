import { useCallback, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Player, Position, Ranking, ThemeModifier } from '../../types';
import { ShareCardGenerator, type ShareCardSize } from './ShareCardGenerator';

type CopyStatus = 'idle' | 'generating' | 'copied' | 'error';

interface ShareButtonProps {
  ranking: Ranking;
  playersById: Record<number, Player>;
  position: Position;
  themeModifier: ThemeModifier;
}

/**
 * A share button that generates a share card image and copies it to the clipboard.
 * Shows size options when expanded and provides feedback on copy status.
 */
export function ShareButton({ ranking, playersById, position, themeModifier }: ShareButtonProps) {
  const [expanded, setExpanded] = useState(false);
  const [copyStatus, setCopyStatus] = useState<CopyStatus>('idle');
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const handleGenerated = useCallback(async (blob: Blob, _size: ShareCardSize) => {
    setCopyStatus('generating');

    try {
      // Try clipboard API with ClipboardItem (image copy)
      if (navigator.clipboard && typeof ClipboardItem !== 'undefined') {
        const item = new ClipboardItem({ 'image/png': blob });
        await navigator.clipboard.write([item]);
        setCopyStatus('copied');
      } else {
        // Fallback: download the image
        downloadBlob(blob, `hot-take-${ranking.letterGrade}-${Date.now()}.png`);
        setCopyStatus('copied');
      }
    } catch {
      // If clipboard write fails (e.g. permissions), fall back to download
      try {
        downloadBlob(blob, `hot-take-${ranking.letterGrade}-${Date.now()}.png`);
        setCopyStatus('copied');
      } catch {
        setCopyStatus('error');
      }
    }

    // Reset status after delay
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setCopyStatus('idle'), 3000);
  }, [ranking.letterGrade]);

  const statusLabel = getStatusLabel(copyStatus);

  return (
    <div className="flex flex-col items-center gap-3 w-full max-w-xs mx-auto">
      {/* Main share button */}
      <motion.button
        whileTap={{ scale: 0.95 }}
        onClick={() => setExpanded((prev) => !prev)}
        className="px-6 py-3 rounded-full bg-nba-gold text-gray-900 font-bold
                   hover:bg-yellow-400 transition-colors shadow-lg shadow-nba-gold/20
                   w-full"
        aria-label="Share your result"
        aria-expanded={expanded}
      >
        {statusLabel}
      </motion.button>

      {/* Expanded size options + canvas generator */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="w-full overflow-hidden"
          >
            <div className="pt-2">
              <p className="text-gray-400 text-xs text-center mb-2">
                Choose a size, and the image will be copied to your clipboard.
              </p>
              <ShareCardGenerator
                ranking={ranking}
                playersById={playersById}
                position={position}
                themeModifier={themeModifier}
                onGenerated={handleGenerated}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getStatusLabel(status: CopyStatus): string {
  switch (status) {
    case 'generating':
      return 'Generating…';
    case 'copied':
      return '✅ Copied to clipboard!';
    case 'error':
      return '❌ Copy failed — try again';
    default:
      return 'Share Result 🔗';
  }
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
