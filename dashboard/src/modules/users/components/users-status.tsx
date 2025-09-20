import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Label } from '@wildosvpn/common/components';
import { StatusType } from '@wildosvpn/common/types';
import { CommonIcons } from '@wildosvpn/common/components/ui/icon';

interface UsersStatusType {
    [key: string]: Omit<StatusType, 'label'> & { statusKey: string };
}

export const UsersStatus: UsersStatusType = {
    active: {
        icon: CommonIcons.PowerCircle,
        statusKey: "active",
        variant: "positive"
    },
    limited: {
        icon: CommonIcons.BrickWall,
        statusKey: "limited",
        variant: "warning"
    },
    expired: {
        icon: CommonIcons.CalendarX,
        statusKey: "expired",
        variant: "warning"
    },
    on_hold: {
        icon: CommonIcons.AlarmClock,
        statusKey: "on_hold",
        variant: "royal"
    },
    error: {
        icon: CommonIcons.ServerCrash,
        statusKey: "error",
        variant: "destructive"
    },
    connecting: {
        icon: CommonIcons.Radio,
        statusKey: "connecting",
        variant: "warning"
    },
    connected: {
        icon: CommonIcons.Cloud,
        statusKey: "connected",
        variant: "positive"
    },
    healthy: {
        icon: CommonIcons.Zap,
        statusKey: "healthy",
        variant: "positive"
    },
    unhealthy: {
        icon: CommonIcons.ZapOff,
        statusKey: "unhealthy",
        variant: "destructive"
    },
}

interface UsersStatusBadgeProps {
    status: StatusType;
}

export const UsersStatusBadge: React.FC<UsersStatusBadgeProps> = ({ status }) => {
    const { t } = useTranslation();
    const { label, icon: Icon } = status;
    
    // If status has a statusKey, use localized label
    const localizedLabel = (status as any).statusKey 
        ? t(`statuses.${(status as any).statusKey}`) 
        : label;
    
    return (
        <Badge variant={status.variant} className="h-6">
            {Icon && <Icon className="mr-1 w-5 h-4" />} <Label className="capitalize">{localizedLabel}</Label>
        </Badge>
    );
};

export default UsersStatusBadge;
