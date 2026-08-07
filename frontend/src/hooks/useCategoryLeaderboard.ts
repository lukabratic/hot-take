import { useState, useEffect, useCallback } from 'react';
import { getCategoryLeaderboard, getAvailableCategories } from '../services/api';
import type { CategoryLeaderboardEntry } from '../services/api';
import type { CategoryType, CategoryValue } from '../types';

/** Scope options for category leaderboards (no 'friends' scope) */
export type CategoryLeaderboardScope = 'today' | 'week' | 'alltime';

interface UseCategoryLeaderboardResult {
  entries: CategoryLeaderboardEntry[];
  loading: boolean;
  error: string | null;
  scope: CategoryLeaderboardScope;
  setScope: (scope: CategoryLeaderboardScope) => void;
  categoryType: CategoryType;
  setCategoryType: (type: CategoryType) => void;
  categoryValue: string;
  setCategoryValue: (value: string) => void;
  availableCategories: Record<string, CategoryValue[]>;
  categoriesLoading: boolean;
  refresh: () => void;
}

/**
 * Hook for fetching and managing category leaderboard data.
 * Supports category selection and scope switching (today, week, alltime).
 *
 * Requirements: 6.2, 6.3, 6.4
 */
export function useCategoryLeaderboard(
  initialScope: CategoryLeaderboardScope = 'today'
): UseCategoryLeaderboardResult {
  const [scope, setScope] = useState<CategoryLeaderboardScope>(initialScope);
  const [categoryType, setCategoryType] = useState<CategoryType>('position');
  const [categoryValue, setCategoryValue] = useState<string>('');
  const [entries, setEntries] = useState<CategoryLeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableCategories, setAvailableCategories] = useState<Record<string, CategoryValue[]>>({});
  const [categoriesLoading, setCategoriesLoading] = useState(true);

  // Fetch available categories on mount
  useEffect(() => {
    let cancelled = false;

    async function fetchCategories() {
      setCategoriesLoading(true);
      try {
        const data = await getAvailableCategories();
        if (!cancelled) {
          setAvailableCategories(data);
          // Set initial category value to the first available value for the current type
          const typeValues = data[categoryType];
          if (typeValues && typeValues.length > 0 && !categoryValue) {
            setCategoryValue(typeValues[0].value);
          }
        }
      } catch {
        // Silent failure for categories — leaderboard will show empty state
      } finally {
        if (!cancelled) {
          setCategoriesLoading(false);
        }
      }
    }

    fetchCategories();
    return () => { cancelled = true; };
  }, []);

  // Update categoryValue when categoryType changes
  useEffect(() => {
    const typeValues = availableCategories[categoryType];
    if (typeValues && typeValues.length > 0) {
      setCategoryValue(typeValues[0].value);
    }
  }, [categoryType, availableCategories]);

  // Fetch leaderboard data when category value or scope changes
  const fetchLeaderboard = useCallback(async () => {
    if (!categoryValue) return;

    setLoading(true);
    setError(null);

    try {
      const data = await getCategoryLeaderboard(categoryValue, scope);
      setEntries(data.entries);
    } catch {
      setError('Failed to load category leaderboard');
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [categoryValue, scope]);

  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);

  return {
    entries,
    loading,
    error,
    scope,
    setScope,
    categoryType,
    setCategoryType,
    categoryValue,
    setCategoryValue,
    availableCategories,
    categoriesLoading,
    refresh: fetchLeaderboard,
  };
}
