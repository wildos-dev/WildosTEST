import { BreakpointGaps } from './types';

// Container padding presets
export const CONTAINER_PADDINGS = {
  none: '',
  sm: 'p-2 sm:p-3 md:p-4',
  md: 'p-4 sm:p-6 md:p-8',
  lg: 'p-6 sm:p-8 md:p-12',
  xl: 'p-8 sm:p-12 md:p-16',
} as const;

// Container size presets
export const CONTAINER_SIZES = {
  sm: 'max-w-sm mx-auto',
  md: 'max-w-md mx-auto',
  lg: 'max-w-lg mx-auto',
  xl: 'max-w-xl mx-auto',
  full: 'w-full',
} as const;

// Gap scales for responsive grids
export const GAP_SCALES: BreakpointGaps = {
  xs: 'gap-1 sm:gap-2',
  sm: 'gap-2 sm:gap-3 md:gap-4',
  md: 'gap-3 sm:gap-4 md:gap-6',
  lg: 'gap-4 sm:gap-6 md:gap-8',
  xl: 'gap-6 sm:gap-8 md:gap-10',
} as const;

// Grid column presets
export const GRID_COLUMNS = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
  5: 'grid-cols-5',
  6: 'grid-cols-6',
  12: 'grid-cols-12',
} as const;