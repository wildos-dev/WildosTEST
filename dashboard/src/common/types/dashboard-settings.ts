export interface DashboardWidgetSettings {
  totalTraffics: boolean;
  usersStats: boolean;
  hostSystemMetrics: boolean;
  allBackendsStats: boolean;
  peakEvents: boolean;
  nodesStats: boolean;
  adminsStats: boolean;
  systemOverview: boolean;
  topUsageNodes: boolean;
  networkActivity: boolean;
  quickActions: boolean;
  subscriptionSettings: boolean;
  recentSubscriptionUpdates: boolean;
  certificateStatus: boolean;
}

export interface DashboardWidgetInfo {
  id: keyof DashboardWidgetSettings;
  name: string;
  description: string;
  category: 'traffic' | 'users' | 'nodes' | 'system' | 'events' | 'admin' | 'metrics' | 'actions' | 'notifications';
  icon?: string;
  defaultVisible: boolean;
}

export const DEFAULT_DASHBOARD_WIDGET_SETTINGS: DashboardWidgetSettings = {
  totalTraffics: true,
  usersStats: true,
  hostSystemMetrics: false,
  allBackendsStats: true,
  peakEvents: false,
  nodesStats: true,
  adminsStats: true,
  systemOverview: true,
  topUsageNodes: false,
  networkActivity: false,
  quickActions: true,
  subscriptionSettings: false,
  recentSubscriptionUpdates: true,
  certificateStatus: false,
};

export const DASHBOARD_WIDGETS_CONFIG: DashboardWidgetInfo[] = [
  {
    id: 'totalTraffics',
    name: 'Total Traffic',
    description: 'Display overall network traffic statistics',
    category: 'traffic',
    icon: 'BarChart3',
    defaultVisible: true,
  },
  {
    id: 'usersStats',
    name: 'Users Statistics',
    description: 'Overview of user activity and status',
    category: 'users',
    icon: 'Users',
    defaultVisible: true,
  },
  {
    id: 'hostSystemMetrics',
    name: 'Host System Metrics',
    description: 'CPU, memory, disk and network metrics',
    category: 'system',
    icon: 'Monitor',
    defaultVisible: false,
  },
  {
    id: 'allBackendsStats',
    name: 'All Backends Stats',
    description: 'Comprehensive backend overview',
    category: 'system',
    icon: 'Layers',
    defaultVisible: true,
  },
  {
    id: 'peakEvents',
    name: 'Peak Events',
    description: 'System resource peak usage alerts',
    category: 'events',
    icon: 'AlertTriangle',
    defaultVisible: false,
  },
  {
    id: 'nodesStats',
    name: 'Nodes Statistics',
    description: 'Statistical overview of all nodes',
    category: 'nodes',
    icon: 'PieChart',
    defaultVisible: true,
  },
  {
    id: 'adminsStats',
    name: 'Admins Statistics',
    description: 'Administrative user statistics',
    category: 'admin',
    icon: 'Shield',
    defaultVisible: true,
  },
  {
    id: 'systemOverview',
    name: 'System Overview',
    description: 'Key system metrics at a glance',
    category: 'system',
    icon: 'Activity',
    defaultVisible: true,
  },
  {
    id: 'topUsageNodes',
    name: 'Top Usage Nodes',
    description: 'Nodes with highest traffic usage',
    category: 'metrics',
    icon: 'TrendingUp',
    defaultVisible: false,
  },
  {
    id: 'networkActivity',
    name: 'Network Activity',
    description: 'Real-time network traffic monitoring',
    category: 'metrics',
    icon: 'Network',
    defaultVisible: false,
  },
  {
    id: 'quickActions',
    name: 'Quick Actions',
    description: 'Shortcuts for common tasks',
    category: 'actions',
    icon: 'Zap',
    defaultVisible: true,
  },
  {
    id: 'subscriptionSettings',
    name: 'Subscription Settings',
    description: 'Manage subscription configuration',
    category: 'actions',
    icon: 'Settings',
    defaultVisible: false,
  },
  {
    id: 'recentSubscriptionUpdates',
    name: 'Recent Updates',
    description: 'Latest subscription changes',
    category: 'notifications',
    icon: 'Bell',
    defaultVisible: true,
  },
  {
    id: 'certificateStatus',
    name: 'Certificate Status',
    description: 'SSL certificate health overview',
    category: 'notifications',
    icon: 'Shield',
    defaultVisible: false,
  },
];

export type DashboardWidgetCategory = DashboardWidgetInfo['category'];

export interface DashboardSettingsContextType {
  settings: DashboardWidgetSettings;
  updateSetting: (widgetId: keyof DashboardWidgetSettings, visible: boolean) => void;
  resetToDefaults: () => void;
  isWidgetVisible: (widgetId: keyof DashboardWidgetSettings) => boolean;
}