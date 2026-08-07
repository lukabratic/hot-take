import { useState, useCallback } from 'react';
import { arrayMove } from '@dnd-kit/sortable';
import type { Player } from '../types';

export interface UseRankingReturn {
  /** Current player order */
  items: Player[];
  /** Whether the user has made at least one reorder */
  hasReordered: boolean;
  /** Handle reorder after drag end */
  handleReorder: (oldIndex: number, newIndex: number) => void;
  /** Get the current player ID order for submission */
  getPlayerOrder: () => number[];
  /** Reset to initial order */
  reset: (players: Player[]) => void;
}

/**
 * Manages the drag-and-drop ranking state.
 * Tracks whether the user has reordered at least once (for submit button activation).
 */
export function useRanking(initialPlayers: Player[]): UseRankingReturn {
  const [items, setItems] = useState<Player[]>(initialPlayers);
  const [hasReordered, setHasReordered] = useState(false);

  const handleReorder = useCallback((oldIndex: number, newIndex: number) => {
    if (oldIndex !== newIndex) {
      setHasReordered(true);
      setItems((prev) => arrayMove(prev, oldIndex, newIndex));
    }
  }, []);

  const getPlayerOrder = useCallback(() => {
    return items.map((p) => p.id);
  }, [items]);

  const reset = useCallback((players: Player[]) => {
    setItems(players);
    setHasReordered(false);
  }, []);

  return {
    items,
    hasReordered,
    handleReorder,
    getPlayerOrder,
    reset,
  };
}
