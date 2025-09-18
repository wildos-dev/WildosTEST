import * as React from 'react';
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
  Button,
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { useTranslation } from 'react-i18next';

interface FilterDrawerProps {
  trigger?: React.ReactNode;
  children: React.ReactNode;
  title?: string;
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function FilterDrawer({ 
  trigger, 
  children, 
  title,
  isOpen,
  onOpenChange 
}: FilterDrawerProps) {
  const { t } = useTranslation();
  
  const defaultTrigger = (
    <Button variant="outline" size="sm" data-testid="button-open-filters">
      <Icon name="Filter" className="h-4 w-4 mr-2" />
      {t('filters', 'Filters')}
    </Button>
  );

  return (
    <Drawer open={isOpen} onOpenChange={onOpenChange}>
      <DrawerTrigger asChild>
        {trigger || defaultTrigger}
      </DrawerTrigger>
      <DrawerContent className="max-h-[85vh]">
        <DrawerHeader className="border-b">
          <DrawerTitle>
            {title || t('filters', 'Filters')}
          </DrawerTitle>
        </DrawerHeader>
        <div className="p-4 overflow-y-auto flex-1">
          {children}
        </div>
      </DrawerContent>
    </Drawer>
  );
}