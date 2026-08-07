import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { AnimatePresence } from 'framer-motion';
import { PlayerCard } from './PlayerCard';
import { HoopIQPlayerCard } from './HoopIQPlayerCard';
import type { Player, ThemeModifier } from '../../types';

interface RankingBoardProps {
  items: Player[];
  onReorder: (oldIndex: number, newIndex: number) => void;
  /** Called when a drag starts — used to lock rubric selection */
  onDragStart?: () => void;
  /** Variant: "default" shows full PlayerCard; "hoopiq" shows stat-line-only HoopIQPlayerCard */
  variant?: 'default' | 'hoopiq';
  /** The theme modifier for the current roll — required when variant is "hoopiq" */
  themeModifier?: ThemeModifier;
}

/**
 * The main ranking interface using @dnd-kit SortableContext with vertical list strategy.
 * Displays rank numbers 1–N beside each player and handles drag-and-drop reordering.
 * Supports a "hoopiq" variant that renders stat-line-only cards without player names.
 */
export function RankingBoard({ items, onReorder, onDragStart, variant = 'default', themeModifier }: RankingBoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex((p) => p.id === active.id);
      const newIndex = items.findIndex((p) => p.id === over.id);
      onReorder(oldIndex, newIndex);
    }
  }

  function handleDragStart() {
    onDragStart?.();
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={items.map((p) => p.id)}
        strategy={verticalListSortingStrategy}
      >
        <div
          className="flex flex-col gap-2"
          role="list"
          aria-label="Player ranking"
        >
          <AnimatePresence>
            {items.map((player, index) =>
              variant === 'hoopiq' && themeModifier ? (
                <HoopIQPlayerCard
                  key={player.id}
                  player={player}
                  rank={index + 1}
                  themeModifier={themeModifier}
                />
              ) : (
                <PlayerCard
                  key={player.id}
                  player={player}
                  rank={index + 1}
                />
              )
            )}
          </AnimatePresence>
        </div>
      </SortableContext>
    </DndContext>
  );
}
