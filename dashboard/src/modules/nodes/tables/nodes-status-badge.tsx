import * as React from 'react';
import { Badge, Label } from '@wildosvpn/common/components';
import { StatusType } from '@wildosvpn/common/types';
import { NodesStatus } from '..';

interface NodesStatusBadgeProps {
    status: StatusType;
}

export const NodesStatusBadge: React.FC<NodesStatusBadgeProps> = ({ status }) => {
    if (!status) {
        return null;
    }
    
    const { label, icon: Icon } = status;

    let badgeVariant: 'outline' | 'destructive' | undefined | null;
    switch (label) {
        case NodesStatus.healthy.label:
            badgeVariant = undefined;
            break;
        case NodesStatus.unhealthy.label:
            badgeVariant = "destructive";
            break;
        case NodesStatus.disabled.label:
            badgeVariant = "outline";
            break;
        case "none":
            return null;
    }

    return (
        <Badge variant={badgeVariant} className="h-6">
            {Icon && <Icon className="mr-1 w-5 h-4" />} <Label className="capitalize">{label}</Label>
        </Badge>
    );
};

export default NodesStatusBadge;
