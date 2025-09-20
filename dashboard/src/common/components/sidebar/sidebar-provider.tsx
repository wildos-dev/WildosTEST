import * as React from "react";
import type { SidebarItemGroup } from "./types";

interface SidebarContextProps {
    sidebar: SidebarItemGroup;
    collapsed: boolean;
    setCollapsed: (state: boolean) => void;
    open?: boolean;
    setOpen?: (state: boolean) => void;
}

// Safe createContext with fallback
export const SidebarContext = (React?.createContext || (() => {
    throw new Error("React is not available - check React imports and build configuration");
}))<SidebarContextProps | null>(null);

export const useSidebarContext = () => {
    const ctx = (React?.useContext || (() => {
        throw new Error("React is not available - check React imports and build configuration");
    }))(SidebarContext);
    if (!ctx)
        throw new Error(
            "Sidebar.* component must be rendered as child of Sidebar ",
        );
    return ctx;
};
