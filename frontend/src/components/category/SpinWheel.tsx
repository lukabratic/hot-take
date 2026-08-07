import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, useAnimation } from 'framer-motion';
import type { CategoryValue } from '../../types';

interface SpinWheelProps {
  /** Available category values to spin through */
  values: CategoryValue[];
  /** Called when spin completes and lands on a value */
  onResult: (value: string) => void;
  /** Whether the wheel is currently disabled */
  disabled?: boolean;
}

/** Height of each item in the spin column (px) */
const ITEM_HEIGHT = 56;

/** Duration of the spin animation in seconds */
const SPIN_DURATION = 2.5;

/** Hold time after landing before firing callback (ms) */
const HOLD_DELAY = 1000;

/**
 * SpinWheel — a slot-machine-style vertical column that cycles through
 * category values and lands on a randomly selected one with deceleration easing.
 */
export function SpinWheel({ values, onResult, disabled = false }: SpinWheelProps) {
  const [isSpinning, setIsSpinning] = useState(false);
  const [resultValue, setResultValue] = useState<string | null>(null);
  const controls = useAnimation();
  const holdTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Only include enabled values for the spin target
  const enabledValues = values.filter((v) => !v.disabled);

  // Cleanup hold timer on unmount
  useEffect(() => {
    return () => {
      if (holdTimerRef.current) clearTimeout(holdTimerRef.current);
    };
  }, []);

  const handleSpin = useCallback(async () => {
    if (isSpinning || disabled || enabledValues.length === 0) return;

    setIsSpinning(true);
    setResultValue(null);

    // Pick a random enabled value to land on
    const targetIndex = Math.floor(Math.random() * enabledValues.length);
    const targetValue = enabledValues[targetIndex];

    // Find the actual index in the full values array for positioning
    const fullIndex = values.findIndex((v) => v.value === targetValue.value);

    // We spin through multiple full cycles + land at the target
    const totalItems = values.length;
    const fullCycles = 3; // spin through 3 full cycles for visual effect
    const totalDistance = (fullCycles * totalItems + fullIndex) * ITEM_HEIGHT;

    // Reset position to top
    await controls.set({ y: 0 });

    // Animate with deceleration
    await controls.start({
      y: -totalDistance,
      transition: {
        duration: SPIN_DURATION,
        ease: [0.2, 0.0, 0.1, 1.0], // custom cubic-bezier for deceleration
      },
    });

    // Show result
    setResultValue(targetValue.value);

    // Hold for 1 second then fire callback
    holdTimerRef.current = setTimeout(() => {
      setIsSpinning(false);
      onResult(targetValue.value);
    }, HOLD_DELAY);
  }, [isSpinning, disabled, enabledValues, values, controls, onResult]);

  // Build the repeating list (cycles + 1 extra to ensure smooth landing)
  const repeatedValues = Array.from({ length: 4 }, () => values).flat();

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Spin viewport */}
      <div
        className="relative w-full max-w-xs h-14 overflow-hidden rounded-lg border border-gray-600 bg-gray-800"
        aria-live="polite"
        aria-label="Category spin wheel"
      >
        {/* Center highlight bar */}
        <div className="absolute inset-0 pointer-events-none z-10 border-2 border-nba-gold rounded-lg" />

        {/* Animated column */}
        <motion.div animate={controls} className="flex flex-col">
          {repeatedValues.map((item, idx) => (
            <div
              key={`${item.value}-${idx}`}
              className={`flex items-center justify-center h-14 text-lg font-semibold shrink-0 ${
                item.disabled ? 'text-gray-600' : 'text-white'
              }`}
            >
              {item.label}
            </div>
          ))}
        </motion.div>
      </div>

      {/* Result display */}
      {resultValue && !isSpinning && (
        <p className="text-nba-gold font-bold text-lg animate-pulse">
          {values.find((v) => v.value === resultValue)?.label}
        </p>
      )}

      {/* Spin button */}
      <button
        onClick={handleSpin}
        disabled={isSpinning || disabled || enabledValues.length === 0}
        className={`px-6 py-3 rounded-lg font-bold text-lg transition-all ${
          isSpinning || disabled || enabledValues.length === 0
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
            : 'bg-nba-gold text-gray-900 hover:bg-yellow-400 active:scale-95'
        }`}
        aria-label="Spin the wheel"
      >
        {isSpinning ? 'Spinning…' : 'Spin'}
      </button>
    </div>
  );
}
