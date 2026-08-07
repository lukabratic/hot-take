interface SubmitButtonProps {
  /** Whether the user has made at least one reorder */
  hasReordered: boolean;
  /** Whether a rubric has been selected */
  hasRubric: boolean;
  /** Whether the submission is in progress */
  isSubmitting: boolean;
  /** Submit handler */
  onSubmit: () => void;
}

/**
 * Submit button that becomes active only after at least one reorder and rubric selection.
 * Shows loading state during submission.
 */
export function SubmitButton({
  hasReordered,
  hasRubric,
  isSubmitting,
  onSubmit,
}: SubmitButtonProps) {
  const isDisabled = !hasReordered || !hasRubric || isSubmitting;

  return (
    <button
      type="button"
      disabled={isDisabled}
      onClick={onSubmit}
      className={`
        w-full py-3 px-6 rounded-lg font-bold text-lg transition-all
        ${isDisabled
          ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
          : 'bg-nba-gold text-gray-900 hover:bg-yellow-400 active:scale-[0.98]'
        }
      `}
      aria-label="Submit ranking"
    >
      {isSubmitting ? (
        <span className="flex items-center justify-center gap-2">
          <svg
            className="animate-spin h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          Submitting…
        </span>
      ) : (
        'Lock It In 🔒'
      )}
    </button>
  );
}
