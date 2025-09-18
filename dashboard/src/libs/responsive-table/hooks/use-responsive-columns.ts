import * as React from 'react';
import { ColumnDef } from "@tanstack/react-table";
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import { BreakpointColumnPreset } from '../types';

export function useResponsiveColumns<T>(
  columns: ColumnDef<T>[],
  presets: BreakpointColumnPreset<T>
) {
  const isMobile = !useScreenBreakpoint('md');
  const isTablet = useScreenBreakpoint('md') && !useScreenBreakpoint('lg');
  const isDesktop = useScreenBreakpoint('lg');

  const visibleColumns = React.useMemo(() => {
    let visibleColumnIds: string[];
    
    if (isMobile) {
      visibleColumnIds = presets.mobile;
    } else if (isTablet) {
      visibleColumnIds = presets.tablet;
    } else {
      visibleColumnIds = presets.desktop;
    }

    return columns.filter(column => {
      const columnId = (column as any).id || (column as any).accessorKey;
      return visibleColumnIds.includes(columnId);
    });
  }, [columns, presets, isMobile, isTablet, isDesktop]);

  return {
    visibleColumns,
    isMobile,
    isTablet,
    isDesktop,
  };
}