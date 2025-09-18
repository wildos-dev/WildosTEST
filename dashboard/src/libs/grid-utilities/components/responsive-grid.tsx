import * as React from 'react';
import { cn } from "@wildosvpn/common/utils";
import { GridProps } from '../types';
import { GAP_SCALES, GRID_COLUMNS } from '../constants';

export function ResponsiveGrid({
  cols = { default: 1, md: 2, lg: 3 },
  gap = 'md',
  className,
  children,
}: GridProps) {
  // Build responsive grid classes
  const gridClasses = React.useMemo(() => {
    const classes = ['grid'];
    
    // Add default columns
    classes.push(GRID_COLUMNS[cols.default as keyof typeof GRID_COLUMNS]);
    
    // Add responsive columns
    if (cols.sm) {
      classes.push(`sm:${GRID_COLUMNS[cols.sm as keyof typeof GRID_COLUMNS]}`);
    }
    if (cols.md) {
      classes.push(`md:${GRID_COLUMNS[cols.md as keyof typeof GRID_COLUMNS]}`);
    }
    if (cols.lg) {
      classes.push(`lg:${GRID_COLUMNS[cols.lg as keyof typeof GRID_COLUMNS]}`);
    }
    if (cols.xl) {
      classes.push(`xl:${GRID_COLUMNS[cols.xl as keyof typeof GRID_COLUMNS]}`);
    }
    
    return classes.join(' ');
  }, [cols]);

  return (
    <div 
      className={cn(
        gridClasses,
        GAP_SCALES[gap],
        className
      )}
      data-testid="responsive-grid"
    >
      {children}
    </div>
  );
}