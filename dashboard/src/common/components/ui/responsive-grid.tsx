import * as React from "react";
import { cn } from "@wildosvpn/common/utils";

interface ResponsiveGridProps {
    children: React.ReactNode;
    className?: string;
    cols?: {
        default?: number;
        sm?: number;
        md?: number;
        lg?: number;
        xl?: number;
    };
    gap?: string;
}

const gridColMap = {
    1: 'grid-cols-1',
    2: 'grid-cols-2', 
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    6: 'grid-cols-6',
} as const;

const smGridColMap = {
    1: 'sm:grid-cols-1',
    2: 'sm:grid-cols-2',
    3: 'sm:grid-cols-3', 
    4: 'sm:grid-cols-4',
    5: 'sm:grid-cols-5',
    6: 'sm:grid-cols-6',
} as const;

const mdGridColMap = {
    1: 'md:grid-cols-1',
    2: 'md:grid-cols-2',
    3: 'md:grid-cols-3',
    4: 'md:grid-cols-4', 
    5: 'md:grid-cols-5',
    6: 'md:grid-cols-6',
} as const;

const lgGridColMap = {
    1: 'lg:grid-cols-1',
    2: 'lg:grid-cols-2',
    3: 'lg:grid-cols-3',
    4: 'lg:grid-cols-4',
    5: 'lg:grid-cols-5', 
    6: 'lg:grid-cols-6',
} as const;

const xlGridColMap = {
    1: 'xl:grid-cols-1',
    2: 'xl:grid-cols-2',
    3: 'xl:grid-cols-3',
    4: 'xl:grid-cols-4',
    5: 'xl:grid-cols-5',
    6: 'xl:grid-cols-6',
} as const;

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
    children,
    className,
    cols = { default: 1, sm: 2, md: 3, lg: 4 },
    gap = "gap-4",
}) => {
    const gridClasses = cn(
        "grid w-full",
        gap,
        cols.default && gridColMap[cols.default as keyof typeof gridColMap],
        cols.sm && smGridColMap[cols.sm as keyof typeof smGridColMap],
        cols.md && mdGridColMap[cols.md as keyof typeof mdGridColMap],
        cols.lg && lgGridColMap[cols.lg as keyof typeof lgGridColMap],
        cols.xl && xlGridColMap[cols.xl as keyof typeof xlGridColMap],
        className
    );

    return (
        <div className={gridClasses}>
            {React.Children.map(children, (child) => (
                <div className="w-full max-w-full min-w-0">
                    {child}
                </div>
            ))}
        </div>
    );
};

ResponsiveGrid.displayName = "ResponsiveGrid";