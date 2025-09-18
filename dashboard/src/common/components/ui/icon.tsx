import * as Icons from 'lucide-react';
import * as React from 'react';

// Type for all available lucide-react icon names
export type IconName = keyof typeof Icons;

// Props interface for Icon component
export interface IconProps extends Omit<React.ComponentPropsWithoutRef<'svg'>, 'name'> {
  name: IconName;
  size?: number | string;
  className?: string;
}

/**
 * Icon wrapper component that provides safe access to lucide-react icons
 * Uses namespace import to avoid TypeScript errors with named imports
 */
export const Icon: React.FC<IconProps> = ({ 
  name, 
  size = 16, 
  className = '', 
  ...props 
}) => {
  // Get the icon component from the Icons namespace
  const IconComponent = Icons[name] as React.ComponentType<any>;
  
  // Fallback to a default icon if the requested icon doesn't exist
  if (!IconComponent) {
    console.warn(`Icon "${String(name)}" not found in lucide-react`);
    return <Icons.AlertCircle className={className} size={size} {...props} />;
  }
  
  return <IconComponent className={className} size={size} {...props} />;
};

// Export commonly used icons as constants for easier migration
export const CommonIcons = {
  // Navigation & UI
  Home: (props: Omit<IconProps, 'name'>) => <Icon name="Home" {...props} />,
  Settings: (props: Omit<IconProps, 'name'>) => <Icon name="Settings" {...props} />,
  Menu: (props: Omit<IconProps, 'name'>) => <Icon name="Menu" {...props} />,
  Search: (props: Omit<IconProps, 'name'>) => <Icon name="Search" {...props} />,
  X: (props: Omit<IconProps, 'name'>) => <Icon name="X" {...props} />,
  
  // Users & Auth
  Users: (props: Omit<IconProps, 'name'>) => <Icon name="Users" {...props} />,
  User: (props: Omit<IconProps, 'name'>) => <Icon name="User" {...props} />,
  UserCheck: (props: Omit<IconProps, 'name'>) => <Icon name="UserCheck" {...props} />,
  UserX: (props: Omit<IconProps, 'name'>) => <Icon name="UserX" {...props} />,
  UserPlus: (props: Omit<IconProps, 'name'>) => <Icon name="UserPlus" {...props} />,
  LogOut: (props: Omit<IconProps, 'name'>) => <Icon name="LogOut" {...props} />,
  ShieldCheck: (props: Omit<IconProps, 'name'>) => <Icon name="ShieldCheck" {...props} />,
  Shield: (props: Omit<IconProps, 'name'>) => <Icon name="Shield" {...props} />,
  
  // System & Infrastructure
  Server: (props: Omit<IconProps, 'name'>) => <Icon name="Server" {...props} />,
  ServerCog: (props: Omit<IconProps, 'name'>) => <Icon name="ServerCog" {...props} />,
  Box: (props: Omit<IconProps, 'name'>) => <Icon name="Box" {...props} />,
  Monitor: (props: Omit<IconProps, 'name'>) => <Icon name="Monitor" {...props} />,
  Activity: (props: Omit<IconProps, 'name'>) => <Icon name="Activity" {...props} />,
  Network: (props: Omit<IconProps, 'name'>) => <Icon name="Network" {...props} />,
  HardDrive: (props: Omit<IconProps, 'name'>) => <Icon name="HardDrive" {...props} />,
  
  // Status & Alerts
  AlertCircle: (props: Omit<IconProps, 'name'>) => <Icon name="AlertCircle" {...props} />,
  AlertTriangle: (props: Omit<IconProps, 'name'>) => <Icon name="AlertTriangle" {...props} />,
  CheckCircle: (props: Omit<IconProps, 'name'>) => <Icon name="CheckCircle" {...props} />,
  Circle: (props: Omit<IconProps, 'name'>) => <Icon name="Circle" {...props} />,
  Loader: (props: Omit<IconProps, 'name'>) => <Icon name="Loader" {...props} />,
  Bell: (props: Omit<IconProps, 'name'>) => <Icon name="Bell" {...props} />,
  
  // Actions
  Edit: (props: Omit<IconProps, 'name'>) => <Icon name="Edit" {...props} />,
  Trash2: (props: Omit<IconProps, 'name'>) => <Icon name="Trash2" {...props} />,
  Plus: (props: Omit<IconProps, 'name'>) => <Icon name="Plus" {...props} />,
  RefreshCw: (props: Omit<IconProps, 'name'>) => <Icon name="RefreshCw" {...props} />,
  Copy: (props: Omit<IconProps, 'name'>) => <Icon name="Copy" {...props} />,
  TrendingUp: (props: Omit<IconProps, 'name'>) => <Icon name="TrendingUp" {...props} />,
  
  // UI Elements
  ChevronDown: (props: Omit<IconProps, 'name'>) => <Icon name="ChevronDown" {...props} />,
  ChevronUp: (props: Omit<IconProps, 'name'>) => <Icon name="ChevronUp" {...props} />,
  ChevronLeft: (props: Omit<IconProps, 'name'>) => <Icon name="ChevronLeft" {...props} />,
  ChevronRight: (props: Omit<IconProps, 'name'>) => <Icon name="ChevronRight" {...props} />,
  MoreHorizontal: (props: Omit<IconProps, 'name'>) => <Icon name="MoreHorizontal" {...props} />,
  
  // Panel & Layout
  PanelLeftClose: (props: Omit<IconProps, 'name'>) => <Icon name="PanelLeftClose" {...props} />,
  PanelLeftOpen: (props: Omit<IconProps, 'name'>) => <Icon name="PanelLeftOpen" {...props} />,
  GripVertical: (props: Omit<IconProps, 'name'>) => <Icon name="GripVertical" {...props} />,
  
  // Internationalization
  Languages: (props: Omit<IconProps, 'name'>) => <Icon name="Languages" {...props} />,
  
  // User Status & States
  AlarmClock: (props: Omit<IconProps, 'name'>) => <Icon name="AlarmClock" {...props} />,
  BrickWall: (props: Omit<IconProps, 'name'>) => <Icon name="Brick" {...props} />,
  CalendarX: (props: Omit<IconProps, 'name'>) => <Icon name="CalendarX" {...props} />,
  Cloud: (props: Omit<IconProps, 'name'>) => <Icon name="Cloud" {...props} />,
  PowerCircle: (props: Omit<IconProps, 'name'>) => <Icon name="Power" {...props} />,
  Radio: (props: Omit<IconProps, 'name'>) => <Icon name="Radio" {...props} />,
  ServerCrash: (props: Omit<IconProps, 'name'>) => <Icon name="ServerCrash" {...props} />,
  Zap: (props: Omit<IconProps, 'name'>) => <Icon name="Zap" {...props} />,
  ZapOff: (props: Omit<IconProps, 'name'>) => <Icon name="ZapOff" {...props} />,
  
  // Misc
  HeartHandshake: (props: Omit<IconProps, 'name'>) => <Icon name="HeartHandshake" {...props} />,
  QrCode: (props: Omit<IconProps, 'name'>) => <Icon name="QrCode" {...props} />,
  Link: (props: Omit<IconProps, 'name'>) => <Icon name="Link" {...props} />,
  Key: (props: Omit<IconProps, 'name'>) => <Icon name="Key" {...props} />,
} as const;

// Default export for easier imports
export default Icon;