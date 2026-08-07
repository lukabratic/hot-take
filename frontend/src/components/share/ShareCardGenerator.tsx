import { useCallback, useRef, useState } from 'react';
import type { LetterGrade, Player, Position, Ranking, ThemeModifier } from '../../types';

/** Share card size presets */
export type ShareCardSize = 'twitter' | 'tiktok';

const CARD_DIMENSIONS: Record<ShareCardSize, { width: number; height: number }> = {
  twitter: { width: 1200, height: 675 },
  tiktok: { width: 1080, height: 1920 },
};

/** Color palette matching the project's theme */
const GRADE_COLORS: Record<LetterGrade, string> = {
  S: '#fdb927', // nba-gold
  A: '#22c55e', // green-500
  B: '#3b82f6', // blue-500
  C: '#f97316', // orange-500
  D: '#ef4444', // red-500
};

const COLORS = {
  background: '#111827', // gray-900
  cardBg: '#1f2937', // gray-800
  text: '#ffffff',
  textMuted: '#9ca3af', // gray-400
  accent: '#fdb927', // nba-gold
  blue: '#1d428a', // nba-blue
  border: '#374151', // gray-700
};

interface ShareCardGeneratorProps {
  ranking: Ranking;
  playersById: Record<number, Player>;
  position: Position;
  themeModifier: ThemeModifier;
  /** Callback when a card blob is generated */
  onGenerated?: (blob: Blob, size: ShareCardSize) => void;
}

/**
 * Renders a share card to an off-screen canvas and produces a PNG blob.
 * The card displays the Roll (Position + Theme), Letter Grade, and the user's
 * ranking order. It explicitly excludes the consensus ranking to prevent spoilers.
 */
export function ShareCardGenerator({
  ranking,
  playersById,
  position,
  themeModifier,
  onGenerated,
}: ShareCardGeneratorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [generating, setGenerating] = useState(false);

  const generateCard = useCallback(
    async (size: ShareCardSize) => {
      const canvas = canvasRef.current;
      if (!canvas) return null;

      const { width, height } = CARD_DIMENSIONS[size];
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) return null;

      setGenerating(true);

      try {
        if (size === 'twitter') {
          drawTwitterCard(ctx, width, height, ranking, playersById, position, themeModifier);
        } else {
          drawTikTokCard(ctx, width, height, ranking, playersById, position, themeModifier);
        }

        const blob = await canvasToBlob(canvas);
        if (blob && onGenerated) {
          onGenerated(blob, size);
        }
        return blob;
      } finally {
        setGenerating(false);
      }
    },
    [ranking, playersById, position, themeModifier, onGenerated]
  );

  return (
    <>
      {/* Off-screen canvas for rendering */}
      <canvas
        ref={canvasRef}
        style={{ display: 'none' }}
        aria-hidden="true"
      />

      <div className="flex flex-col gap-2 w-full">
        <button
          onClick={() => generateCard('twitter')}
          disabled={generating}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                     bg-gray-700 text-white font-medium text-sm
                     hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          aria-label="Generate share card for Twitter (1200 by 675 pixels)"
        >
          {generating ? (
            <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
          ) : (
            <span aria-hidden="true">🐦</span>
          )}
          Twitter / X (1200×675)
        </button>

        <button
          onClick={() => generateCard('tiktok')}
          disabled={generating}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                     bg-gray-700 text-white font-medium text-sm
                     hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          aria-label="Generate share card for TikTok (1080 by 1920 pixels)"
        >
          {generating ? (
            <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
          ) : (
            <span aria-hidden="true">🎵</span>
          )}
          TikTok Story (1080×1920)
        </button>
      </div>
    </>
  );
}

// ─── Canvas Drawing Helpers ───────────────────────────────────────────────────

function canvasToBlob(canvas: HTMLCanvasElement): Promise<Blob | null> {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), 'image/png');
  });
}

function drawRoundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function drawGradeBadge(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  grade: LetterGrade
) {
  const color = GRADE_COLORS[grade];

  // Glow effect
  ctx.save();
  ctx.shadowColor = color;
  ctx.shadowBlur = radius * 0.4;

  // Badge circle
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.restore();

  // Grade letter
  ctx.fillStyle = '#1f2937';
  ctx.font = `bold ${radius * 1.2}px system-ui, -apple-system, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(grade, x, y + 2);
}

function drawPlayerList(
  ctx: CanvasRenderingContext2D,
  x: number,
  startY: number,
  playerOrder: number[],
  playersById: Record<number, Player>,
  fontSize: number,
  lineHeight: number
) {
  ctx.textAlign = 'left';

  for (let i = 0; i < playerOrder.length; i++) {
    const player = playersById[playerOrder[i]];
    const name = player?.name ?? `Player #${playerOrder[i]}`;
    const yPos = startY + i * lineHeight;

    // Rank number
    ctx.fillStyle = COLORS.accent;
    ctx.font = `bold ${fontSize}px system-ui, -apple-system, sans-serif`;
    ctx.fillText(`${i + 1}.`, x, yPos);

    // Player name
    ctx.fillStyle = COLORS.text;
    ctx.font = `${fontSize}px system-ui, -apple-system, sans-serif`;
    ctx.fillText(name, x + fontSize * 2, yPos);
  }
}

// ─── Twitter Card Layout (1200×675) ──────────────────────────────────────────

function drawTwitterCard(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  ranking: Ranking,
  playersById: Record<number, Player>,
  position: Position,
  themeModifier: ThemeModifier
) {
  // Background
  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, width, height);

  // Subtle gradient overlay
  const grad = ctx.createLinearGradient(0, 0, width, height);
  grad.addColorStop(0, 'rgba(29, 66, 138, 0.15)');
  grad.addColorStop(1, 'rgba(253, 185, 39, 0.05)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);

  // Card border
  drawRoundedRect(ctx, 20, 20, width - 40, height - 40, 16);
  ctx.strokeStyle = COLORS.border;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Title
  ctx.fillStyle = COLORS.accent;
  ctx.font = 'bold 36px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('🔥 HOT TAKE', 60, 80);

  // Roll info (Position + Theme)
  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 28px system-ui, -apple-system, sans-serif';
  ctx.fillText(`${position} · ${themeModifier}`, 60, 130);

  // Grade badge on the right
  drawGradeBadge(ctx, width - 160, 150, 70, ranking.letterGrade);

  // Distance text below badge
  ctx.fillStyle = COLORS.textMuted;
  ctx.font = '18px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(
    ranking.kendallTauDistance === 0
      ? 'Perfect!'
      : `${ranking.kendallTauDistance} swap${ranking.kendallTauDistance !== 1 ? 's' : ''}`,
    width - 160,
    240
  );

  // Player ranking list
  drawPlayerList(ctx, 60, 200, ranking.playerOrder, playersById, 26, 54);

  // Footer
  ctx.fillStyle = COLORS.textMuted;
  ctx.font = '16px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('Can you beat my ranking? 🏀', 60, height - 50);

  // Rubric indicator
  ctx.textAlign = 'right';
  ctx.fillText(
    `Scored: ${ranking.rubric === 'analytics' ? 'Analytics' : 'Reputation'} Rubric`,
    width - 60,
    height - 50
  );
}

// ─── TikTok Card Layout (1080×1920) ─────────────────────────────────────────

function drawTikTokCard(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  ranking: Ranking,
  playersById: Record<number, Player>,
  position: Position,
  themeModifier: ThemeModifier
) {
  // Background
  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, width, height);

  // Gradient overlay
  const grad = ctx.createLinearGradient(0, 0, 0, height);
  grad.addColorStop(0, 'rgba(29, 66, 138, 0.2)');
  grad.addColorStop(0.5, 'rgba(0, 0, 0, 0)');
  grad.addColorStop(1, 'rgba(253, 185, 39, 0.1)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);

  // Card border
  drawRoundedRect(ctx, 30, 30, width - 60, height - 60, 24);
  ctx.strokeStyle = COLORS.border;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Title
  ctx.fillStyle = COLORS.accent;
  ctx.font = 'bold 56px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('🔥 HOT TAKE', width / 2, 150);

  // Subtitle
  ctx.fillStyle = COLORS.textMuted;
  ctx.font = '28px system-ui, -apple-system, sans-serif';
  ctx.fillText('NBA Ranking Game', width / 2, 200);

  // Roll info
  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 40px system-ui, -apple-system, sans-serif';
  ctx.fillText(`${position}`, width / 2, 320);
  ctx.font = '32px system-ui, -apple-system, sans-serif';
  ctx.fillStyle = COLORS.textMuted;
  ctx.fillText(themeModifier, width / 2, 375);

  // Grade badge centered
  drawGradeBadge(ctx, width / 2, 530, 100, ranking.letterGrade);

  // Distance text
  ctx.fillStyle = COLORS.textMuted;
  ctx.font = '26px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(
    ranking.kendallTauDistance === 0
      ? 'Perfect match!'
      : `${ranking.kendallTauDistance} swap${ranking.kendallTauDistance !== 1 ? 's' : ''} from consensus`,
    width / 2,
    660
  );

  // Divider
  ctx.strokeStyle = COLORS.border;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(120, 720);
  ctx.lineTo(width - 120, 720);
  ctx.stroke();

  // "My Ranking" header
  ctx.fillStyle = COLORS.accent;
  ctx.font = 'bold 32px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('My Ranking', width / 2, 790);

  // Player ranking list (centered)
  const listStartY = 870;
  const lineHeight = 80;
  const fontSize = 36;

  ctx.textAlign = 'left';
  const listX = 160;

  for (let i = 0; i < ranking.playerOrder.length; i++) {
    const player = playersById[ranking.playerOrder[i]];
    const name = player?.name ?? `Player #${ranking.playerOrder[i]}`;
    const yPos = listStartY + i * lineHeight;

    // Rank badge
    ctx.fillStyle = COLORS.accent;
    ctx.font = `bold ${fontSize}px system-ui, -apple-system, sans-serif`;
    ctx.fillText(`${i + 1}.`, listX, yPos);

    // Name
    ctx.fillStyle = COLORS.text;
    ctx.font = `${fontSize}px system-ui, -apple-system, sans-serif`;
    ctx.fillText(name, listX + fontSize * 2, yPos);
  }

  // Rubric badge
  const rubricY = listStartY + ranking.playerOrder.length * lineHeight + 60;
  ctx.fillStyle = COLORS.textMuted;
  ctx.font = '24px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(
    `Scored: ${ranking.rubric === 'analytics' ? 'Analytics' : 'Reputation'} Rubric`,
    width / 2,
    rubricY
  );

  // Footer CTA
  ctx.fillStyle = COLORS.accent;
  ctx.font = 'bold 30px system-ui, -apple-system, sans-serif';
  ctx.fillText('Can you beat my ranking? 🏀', width / 2, height - 120);

  ctx.fillStyle = COLORS.textMuted;
  ctx.font = '22px system-ui, -apple-system, sans-serif';
  ctx.fillText('Play now at hottake.game', width / 2, height - 70);
}

export { CARD_DIMENSIONS };
