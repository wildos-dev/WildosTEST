import * as React from "react";
import type { SidebarItemGroup } from "./types";

interface SidebarContextProps {
    sidebar: SidebarItemGroup;
    collapsed: boolean;
    setCollapsed: (state: boolean) => void;
    open?: boolean;
    setOpen?: (state: boolean) => void;
}

export const SidebarContext = React.createContext<SidebarContextProps | null>(null);

export const useSidebarContext = () => {
    const ctx = React.useContext(SidebarContext);
    if (!ctx)
        throw new Error(
            "Sidebar.* component must be rendered as child of Sidebar ",
        );
    return ctx;
};
