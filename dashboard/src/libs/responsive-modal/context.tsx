import * as React from 'react';
import { ResponsiveModalContextValue } from './types';

export const ResponsiveModalContext = React.createContext<ResponsiveModalContextValue | null>(null);

export function useResponsiveModal() {
  const context = React.useContext(ResponsiveModalContext);
  if (!context) {
    throw new Error('useResponsiveModal must be used within a ResponsiveModal');
  }
  return context;
}