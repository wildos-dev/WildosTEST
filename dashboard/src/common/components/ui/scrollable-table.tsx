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
        <div className={cn("w-full max-w-full overflow-x-auto", className)}>
            <div style={{ minWidth }} className="w-full">
                {children}
            </div>
        </div>
    );
};

ScrollableTable.displayName = "ScrollableTable";