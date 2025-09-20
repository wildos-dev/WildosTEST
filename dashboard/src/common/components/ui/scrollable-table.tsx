import * as React from "react";
import { cn } from "@wildosvpn/common/utils";

interface ScrollableTableProps {
    children: React.ReactNode;
    className?: string;
    minWidth?: string;
}

export const ScrollableTable: React.FC<ScrollableTableProps> = ({
    children,
    className,
    minWidth = "640px",
}) => {
    return (
        <div className={cn("w-full max-w-full overflow-x-auto overscroll-x-contain scrollbar-thin", className)}>
            <div style={{ minWidth }} className="w-full min-w-0">
                {children}
            </div>
        </div>
    );
};

ScrollableTable.displayName = "ScrollableTable";