import * as React from "react";
import type { ImperativePanelHandle } from "react-resizable-panels";

export const usePanelToggle = (isDesktop: boolean) => {
    const [collapsed, setCollapsed] = React.useState(false);
    const panelRef = React.useRef<ImperativePanelHandle>(null);
    const [open, setOpen] = React.useState(false);

    const toggleCollapse = () => {
        const panel = panelRef.current;
        if (isDesktop && panel) {
            collapsed ? panel.expand() : panel.collapse();
            setCollapsed(!collapsed);
            setOpen(false);
        }
    };

    const toggleOpen = () => {
        if (!isDesktop) {
            setCollapsed(false);
            setOpen(!open);
        }
    };

    return {
        collapsed,
        open,
        panelRef,
        setCollapsed,
        setOpen,
        toggleCollapse,
        toggleOpen,
    };
};
