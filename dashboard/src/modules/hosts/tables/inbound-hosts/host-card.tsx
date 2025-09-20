import * as React from 'react';
import { HostType } from "@wildosvpn/modules/hosts";
import {
    Card,
    CardHeader,
    CardContent,
    CardFooter,
    Badge,
    Button
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import i18n from "@wildosvpn/features/i18n";
import {
    type ColumnActions
} from "@wildosvpn/libs/entity-table";

interface HostCardProps {
    entity: HostType;
    actions: ColumnActions<HostType>;
    onRowClick?: (entity: HostType) => void;
}

export const HostCard: React.FC<HostCardProps> = ({ entity: host, actions, onRowClick }) => {
    const handleCardClick = () => {
        onRowClick?.(host);
    };

    const handleActionClick = (e: React.MouseEvent) => {
        e.stopPropagation();
    };

    const isActive = !host.is_disabled;

    return (
        <Card 
            className="w-full cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={handleCardClick}
            data-testid={`card-host-${host.id}`}
        >
            <CardHeader className="pb-3">
                {/* Header: Remark + Status */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                        <span className="font-medium truncate" data-testid={`text-remark-${host.id}`}>
                            {host.remark}
                        </span>
                    </div>
                    <Badge 
                        variant={isActive ? "default" : "secondary"} 
                        className="text-xs"
                        data-testid={`status-host-${host.id}`}
                    >
                        {isActive ? i18n.t('active') : i18n.t('disabled')}
                    </Badge>
                </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
                {/* Address and Port Info */}
                <div className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">
                        {i18n.t('address')}
                    </div>
                    <div className="text-sm" data-testid={`text-address-${host.id}`}>
                        {host.address}:{host.port}
                    </div>
                </div>

                {/* Type and Inbound Details */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">
                            {i18n.t('type')}
                        </div>
                        <Badge variant="outline" className="text-xs">
                            {'TCP'}
                        </Badge>
                    </div>
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">
                            {i18n.t('inbound')}
                        </div>
                        <Badge variant="secondary" className="text-xs">
                            {i18n.t('inbound')}
                        </Badge>
                    </div>
                </div>
            </CardContent>

            <CardFooter className="pt-2" onClick={handleActionClick}>
                {/* Action Buttons - Edit and Delete */}
                <div className="flex gap-2 w-full justify-end">
                    <Button
                        variant="secondary"
                        size="touch-sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            actions.onEdit?.(host);
                        }}
                        className="min-w-11 size-11"
                        title={i18n.t('edit')}
                        data-testid={`button-edit-${host.id}`}
                    >
                        <Icon name="Edit" className="h-5 w-5" />
                    </Button>
                    <Button
                        variant="destructive" 
                        size="touch-sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            actions.onDelete?.(host);
                        }}
                        className="min-w-11 size-11"
                        title={i18n.t('delete')}
                        data-testid={`button-delete-${host.id}`}
                    >
                        <Icon name="Trash2" className="h-5 w-5" />
                    </Button>
                </div>
            </CardFooter>
        </Card>
    );
};