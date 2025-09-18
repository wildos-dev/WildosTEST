import { ColumnDef } from "@tanstack/react-table";

export interface BreakpointColumnPreset<TData = any> {
  mobile: string[];  // Column IDs visible on mobile
  tablet: string[];  // Column IDs visible on tablet  
  desktop: string[]; // Column IDs visible on desktop
}

export interface CardRowProps<TData> {
  row: TData;
  columns: ColumnDef<TData>[];
  onRowClick?: (row: TData) => void;
  className?: string;
}

export interface ResponsiveTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];
  columnPresets: BreakpointColumnPreset<TData>;
  renderCard?: (props: CardRowProps<TData>) => React.ReactNode;
  enableCardView?: boolean;
  cardViewBreakpoint?: 'sm' | 'md' | 'lg';
  onRowClick?: (row: TData) => void;
  stickyHeader?: boolean;
  className?: string;
}