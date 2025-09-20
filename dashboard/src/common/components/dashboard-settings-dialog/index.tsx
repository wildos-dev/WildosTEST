import * as React from 'react';
import { Icon } from '@wildosvpn/common/components';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Switch,
  ScrollArea,
  Separator,
} from '@wildosvpn/common/components';
import { useDashboardSettings } from '@wildosvpn/common/hooks';
import {
  DASHBOARD_WIDGETS_CONFIG,
  DashboardWidgetCategory,
  DashboardWidgetInfo,
} from '@wildosvpn/common/types';

interface DashboardSettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const WidgetCategoryIcon: Record<DashboardWidgetCategory, string> = {
  traffic: '📊',
  users: '👥',
  nodes: '🖥️',
  system: '⚙️',
  events: '⚠️',
  admin: '🛡️',
  metrics: '📈',
  actions: '⚡',
  notifications: '🔔',
};

const WidgetCategoryLabel: Record<DashboardWidgetCategory, string> = {
  traffic: 'Traffic Analytics',
  users: 'User Management',
  nodes: 'Node Monitoring',
  system: 'System Metrics',
  events: 'Event Monitoring',
  admin: 'Administration',
  metrics: 'Performance Metrics',
  actions: 'Quick Actions',
  notifications: 'Notifications & Status',
};

const groupWidgetsByCategory = (widgets: DashboardWidgetInfo[]) => {
  return widgets.reduce((acc, widget) => {
    if (!acc[widget.category]) {
      acc[widget.category] = [];
    }
    acc[widget.category].push(widget);
    return acc;
  }, {} as Record<DashboardWidgetCategory, DashboardWidgetInfo[]>);
};

export const DashboardSettingsDialog: React.FC<DashboardSettingsDialogProps> = ({
  open,
  onOpenChange,
}) => {
  const { updateSetting, resetToDefaults, isWidgetVisible } = useDashboardSettings();

  const widgetsByCategory = groupWidgetsByCategory(DASHBOARD_WIDGETS_CONFIG);
  const categories = Object.keys(widgetsByCategory) as DashboardWidgetCategory[];

  const handleReset = () => {
    resetToDefaults();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Icon name="Settings" className="h-5 w-5" />
            Dashboard Settings
          </DialogTitle>
          <DialogDescription>
            Customize which widgets are visible on your dashboard. Changes are automatically saved.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 px-1">
          <div className="space-y-6">
            {categories.map((category) => {
              const widgets = widgetsByCategory[category];
              
              return (
                <div key={category} className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{WidgetCategoryIcon[category]}</span>
                    <h3 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground">
                      {WidgetCategoryLabel[category]}
                    </h3>
                  </div>
                  
                  <div className="space-y-3 pl-6">
                    {widgets.map((widget) => (
                      <div
                        key={widget.id}
                        className="flex items-start justify-between space-x-4 rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium text-sm leading-none">
                              {widget.name}
                            </h4>
                            {widget.defaultVisible && (
                              <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                                Default
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {widget.description}
                          </p>
                        </div>
                        <Switch
                          checked={isWidgetVisible(widget.id)}
                          onCheckedChange={(checked) => updateSetting(widget.id, checked)}
                          aria-label={`Toggle ${widget.name} widget`}
                        />
                      </div>
                    ))}
                  </div>
                  
                  {category !== categories[categories.length - 1] && (
                    <Separator className="mt-6" />
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleReset}
            className="flex items-center gap-2"
          >
            <Icon name="RotateCcw" className="h-4 w-4" />
            Reset to Defaults
          </Button>
          <Button onClick={() => onOpenChange(false)}>
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};