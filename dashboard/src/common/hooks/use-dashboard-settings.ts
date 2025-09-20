import * as React from 'react';
import {
  DashboardWidgetSettings,
  DEFAULT_DASHBOARD_WIDGET_SETTINGS,
  DashboardSettingsContextType,
} from '@wildosvpn/common/types';

const DASHBOARD_SETTINGS_KEY = 'wildos-dashboard-widget-settings';

export const useDashboardSettings = (): DashboardSettingsContextType => {
  const [settings, setSettings] = React.useState<DashboardWidgetSettings>(
    DEFAULT_DASHBOARD_WIDGET_SETTINGS
  );

  // Load settings from localStorage on mount
  React.useEffect(() => {
    try {
      const savedSettings = localStorage.getItem(DASHBOARD_SETTINGS_KEY);
      if (savedSettings) {
        const parsedSettings = JSON.parse(savedSettings) as DashboardWidgetSettings;
        // Merge with defaults to ensure all keys exist
        const mergedSettings = { ...DEFAULT_DASHBOARD_WIDGET_SETTINGS, ...parsedSettings };
        setSettings(mergedSettings);
      }
    } catch (error) {
      console.warn('Failed to load dashboard settings from localStorage:', error);
    }
  }, []);

  // Save settings to localStorage whenever they change
  React.useEffect(() => {
    try {
      localStorage.setItem(DASHBOARD_SETTINGS_KEY, JSON.stringify(settings));
    } catch (error) {
      console.warn('Failed to save dashboard settings to localStorage:', error);
    }
  }, [settings]);

  const updateSetting = React.useCallback(
    (widgetId: keyof DashboardWidgetSettings, visible: boolean) => {
      setSettings((prev) => ({
        ...prev,
        [widgetId]: visible,
      }));
    },
    []
  );

  const resetToDefaults = React.useCallback(() => {
    setSettings(DEFAULT_DASHBOARD_WIDGET_SETTINGS);
  }, []);

  const isWidgetVisible = React.useCallback(
    (widgetId: keyof DashboardWidgetSettings) => {
      return settings[widgetId];
    },
    [settings]
  );

  return {
    settings,
    updateSetting,
    resetToDefaults,
    isWidgetVisible,
  };
};