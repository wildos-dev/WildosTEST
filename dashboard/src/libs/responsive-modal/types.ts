import * as React from 'react';

export interface ResponsiveModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  trigger?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  breakpoint?: 'sm' | 'md' | 'lg';
  className?: string;
  contentClassName?: string;
  headerClassName?: string;
  footerClassName?: string;
  disableOutsideClick?: boolean;
}

export interface ResponsiveModalContextValue {
  isDrawer: boolean;
  onClose: () => void;
}