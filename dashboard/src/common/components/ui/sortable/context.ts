import type {
    DraggableSyntheticListeners,
} from "@dnd-kit/core"
import * as React from 'react';

interface SortableItemContextProps {
    attributes: React.HTMLAttributes<HTMLElement>
    listeners: DraggableSyntheticListeners | undefined
}

// Safe createContext with fallback
export const SortableItemContext = (React?.createContext || (() => {
    throw new Error("React is not available - check React imports and build configuration");
}))<SortableItemContextProps>({
    attributes: {},
    listeners: undefined,
})
