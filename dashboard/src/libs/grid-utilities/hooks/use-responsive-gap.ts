import * as React from 'react';
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";

export function useResponsiveGap() {
  const isSm = useScreenBreakpoint('sm');
  const isMd = useScreenBreakpoint('md');
  const isLg = useScreenBreakpoint('lg');

  const gap = React.useMemo(() => {
    if (isLg) return 'lg';
    if (isMd) return 'md';
    if (isSm) return 'sm';
    return 'xs';
  }, [isSm, isMd, isLg]);

  const gapClass = React.useMemo(() => {
    switch (gap) {
      case 'xs': return 'gap-1';
      case 'sm': return 'gap-2';
      case 'md': return 'gap-4';
      case 'lg': return 'gap-6';
      default: return 'gap-2';
    }
  }, [gap]);

  return {
    gap,
    gapClass,
    isSm,
    isMd,
    isLg,
  };
}