import { useState, useEffect, useCallback } from 'react';
import { getAvailableCategories, type AvailableCategoriesResponse } from '../../services/api';
import { SpinWheel } from './SpinWheel';
import { PickGrid } from './PickGrid';
import type { CategoryType, CategoryValue, SelectionMode } from '../../types';

interface CategorySelectorProps {
  /** Called when a category is selected (via spin or pick) */
  onCategorySelect: (type: CategoryType, value: string) => void;
}

/** Tab definitions for category types */
const CATEGORY_TABS: { type: CategoryType; label: string }[] = [
  { type: 'all', label: 'All' },
  { type: 'position', label: 'Position' },
  { type: 'team', label: 'Team' },
  { type: 'decade', label: 'Decade' },
  { type: 'conference', label: 'Conference' },
];

/**
 * CategorySelector — top-level component for choosing a category before a round.
 *
 * Features:
 * - Tab bar switching between Position / Team / Decade / Conference
 * - Toggle between Spin and Pick modes
 * - Disables interaction while spin is running
 * - Emits onCategorySelect(type, value) on selection
 */
export function CategorySelector({ onCategorySelect }: CategorySelectorProps) {
  const [activeTab, setActiveTab] = useState<CategoryType>('position');
  const [mode, setMode] = useState<SelectionMode>('spin');
  const [categories, setCategories] = useState<AvailableCategoriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSpinning, setIsSpinning] = useState(false);

  // Fetch available categories on mount
  useEffect(() => {
    async function fetchCategories() {
      try {
        setLoading(true);
        const data = await getAvailableCategories();
        setCategories(data);
      } catch {
        setError('Failed to load categories. Please try again.');
      } finally {
        setLoading(false);
      }
    }
    fetchCategories();
  }, []);

  // Current values for the active tab
  const currentValues: CategoryValue[] = categories?.[activeTab] ?? [];

  // Handle spin result
  const handleSpinResult = useCallback(
    (value: string) => {
      setIsSpinning(false);
      onCategorySelect(activeTab, value);
    },
    [activeTab, onCategorySelect]
  );

  // Handle pick selection
  const handlePickSelect = useCallback(
    (value: string) => {
      onCategorySelect(activeTab, value);
    },
    [activeTab, onCategorySelect]
  );

  // Handle tab change
  const handleTabChange = useCallback(
    (type: CategoryType) => {
      if (isSpinning) return; // disable tab switching during spin
      setActiveTab(type);
      // "All" category doesn't support spin — force pick mode
      if (type === 'all') {
        setMode('pick');
      }
    },
    [isSpinning]
  );

  // Handle mode toggle
  const handleModeToggle = useCallback(
    (newMode: SelectionMode) => {
      if (isSpinning) return; // disable mode switching during spin
      setMode(newMode);
    },
    [isSpinning]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin h-6 w-6 border-3 border-nba-gold border-t-transparent rounded-full mx-auto" />
          <p className="text-gray-400 mt-3 text-sm">Loading categories…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-3 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Category Type Tabs */}
      <nav aria-label="Category type selection">
        <div className="flex gap-1 p-1 bg-gray-800 rounded-lg">
          {CATEGORY_TABS.map((tab) => (
            <button
              key={tab.type}
              onClick={() => handleTabChange(tab.type)}
              disabled={isSpinning}
              className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all ${
                activeTab === tab.type
                  ? 'bg-gray-700 text-white shadow-sm'
                  : isSpinning
                  ? 'text-gray-600 cursor-not-allowed'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
              }`}
              aria-pressed={activeTab === tab.type}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Mode Toggle (Spin / Pick) — hidden for "All" category */}
      {activeTab !== 'all' && (
        <div className="flex justify-center">
          <div className="inline-flex gap-1 p-1 bg-gray-800 rounded-lg">
            <button
              onClick={() => handleModeToggle('spin')}
              disabled={isSpinning}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                mode === 'spin'
                  ? 'bg-nba-gold text-gray-900'
                  : isSpinning
                  ? 'text-gray-600 cursor-not-allowed'
                  : 'text-gray-400 hover:text-white'
              }`}
              aria-pressed={mode === 'spin'}
            >
              🎰 Spin
            </button>
            <button
              onClick={() => handleModeToggle('pick')}
              disabled={isSpinning}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                mode === 'pick'
                  ? 'bg-nba-gold text-gray-900'
                  : isSpinning
                  ? 'text-gray-600 cursor-not-allowed'
                  : 'text-gray-400 hover:text-white'
              }`}
              aria-pressed={mode === 'pick'}
            >
              🎯 Pick
            </button>
          </div>
        </div>
      )}

      {/* Selection Area */}
      <div className="min-h-[200px]">
        {mode === 'spin' ? (
          <SpinWheel
            values={currentValues}
            onResult={handleSpinResult}
            disabled={isSpinning}
          />
        ) : (
          <PickGrid
            values={currentValues}
            onSelect={handlePickSelect}
            disabled={isSpinning}
          />
        )}
      </div>
    </div>
  );
}
