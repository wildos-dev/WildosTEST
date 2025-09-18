export interface ContainerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  children: React.ReactNode;
}

export interface GridProps {
  cols?: {
    default: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  children: React.ReactNode;
}

export interface TruncateTextProps {
  text: string;
  maxLength?: number;
  showTooltip?: boolean;
  className?: string;
  tooltipSide?: 'top' | 'right' | 'bottom' | 'left';
}

export type BreakpointGaps = {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
};