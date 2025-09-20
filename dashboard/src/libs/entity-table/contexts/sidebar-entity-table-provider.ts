import * as React from "react";
import {
    type SidebarEntityCardSectionsProps
} from "@wildosvpn/libs/entity-table/components";

interface SidebarEntityTableContextProps<SData> {
    sidebarEntityId?: string;
    setSidebarEntityId: (s: string | undefined) => void;
    sidebarEntities: SData[];
    sidebarCardProps: SidebarEntityCardSectionsProps<SData>;
}

// Safe createContext with fallback
export const SidebarEntityTableContext = (React?.createContext || (() => {
    throw new Error("React is not available - check React imports and build configuration");
}))<SidebarEntityTableContextProps<any> | null>(null);

export const useSidebarEntityTableContext = () => {
    const ctx = (React?.useContext || (() => {
        throw new Error("React is not available - check React imports and build configuration");
    }))(SidebarEntityTableContext);
    if (!ctx)
        throw new Error('SidebarEntityTable.* component must be rendered as child of SidebarEntityTable');
    return ctx;
}
