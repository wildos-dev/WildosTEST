import * as React from 'react';
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import { cn } from "@wildosvpn/common/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@wildosvpn/common/components";

import { ResponsiveModalProps } from '../types';
import { ResponsiveModalContext } from '../context';

export function ResponsiveModal({
  isOpen,
  onOpenChange,
  title,
  description,
  children,
  footer,
  trigger,
  size = 'md',
  breakpoint = 'md',
  className,
  contentClassName,
  headerClassName,
  footerClassName,
  disableOutsideClick = false,
}: ResponsiveModalProps) {
  // Call hooks at the top level
  const isSm = useScreenBreakpoint('sm');
  const isMd = useScreenBreakpoint('md');
  const isLg = useScreenBreakpoint('lg');
  
  // Determine whether to use drawer based on breakpoint
  const isDrawer = React.useMemo(() => {
    switch (breakpoint) {
      case 'sm': return !isSm;
      case 'md': return !isMd;
      case 'lg': return !isLg;
      default: return !isMd;
    }
  }, [breakpoint, isSm, isMd, isLg]);

  const handleClose = React.useCallback(() => {
    onOpenChange(false);
  }, [onOpenChange]);

  const contextValue = React.useMemo(() => ({
    isDrawer,
    onClose: handleClose,
  }), [isDrawer, handleClose]);

  // Dialog size classes
  const getSizeClass = (size: string) => {
    switch (size) {
      case 'sm': return 'max-w-sm';
      case 'md': return 'max-w-md';
      case 'lg': return 'max-w-lg';
      case 'xl': return 'max-w-xl';
      case 'full': return 'max-w-full h-full';
      default: return 'max-w-md';
    }
  };

  const commonHeader = (
    <>
      {title && (
        isDrawer ? (
          <DrawerTitle className={headerClassName}>{title}</DrawerTitle>
        ) : (
          <DialogTitle className={headerClassName}>{title}</DialogTitle>
        )
      )}
      {description && (
        isDrawer ? (
          <DrawerDescription className="text-muted-foreground">
            {description}
          </DrawerDescription>
        ) : (
          <DialogDescription className="text-muted-foreground">
            {description}
          </DialogDescription>
        )
      )}
    </>
  );

  const commonFooter = footer && (
    isDrawer ? (
      <DrawerFooter className={footerClassName}>
        {footer}
      </DrawerFooter>
    ) : (
      <DialogFooter className={footerClassName}>
        {footer}
      </DialogFooter>
    )
  );

  const content = (
    <ResponsiveModalContext.Provider value={contextValue}>
      <div className={cn("flex flex-col", contentClassName)}>
        {children}
      </div>
    </ResponsiveModalContext.Provider>
  );

  if (isDrawer) {
    return (
      <Drawer 
        open={isOpen} 
        onOpenChange={onOpenChange}
        dismissible={!disableOutsideClick}
      >
        {trigger && <DrawerTrigger asChild>{trigger}</DrawerTrigger>}
        <DrawerContent 
          className={cn("max-h-[95vh] flex flex-col", className)}
          onInteractOutside={disableOutsideClick ? (e) => e.preventDefault() : undefined}
        >
          {(title || description) && (
            <DrawerHeader className="border-b flex-shrink-0">
              {commonHeader}
            </DrawerHeader>
          )}
          
          <div className="flex-1 overflow-y-auto p-4">
            {content}
          </div>
          
          {commonFooter}
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Dialog 
      open={isOpen} 
      onOpenChange={onOpenChange}
    >
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent 
        className={cn(
          getSizeClass(size),
          "flex flex-col max-h-[90vh]",
          className
        )}
        onInteractOutside={disableOutsideClick ? (e) => e.preventDefault() : undefined}
      >
        {(title || description) && (
          <DialogHeader className="flex-shrink-0">
            {commonHeader}
          </DialogHeader>
        )}
        
        <div className="flex-1 overflow-y-auto">
          {content}
        </div>
        
        {commonFooter}
      </DialogContent>
    </Dialog>
  );
}