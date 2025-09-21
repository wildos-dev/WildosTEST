import * as React from 'react';
import { ServiceType } from "@wildosvpn/modules/services";
import { Card, CardContent, CardHeader, Button, Checkbox } from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { useTranslation } from "react-i18next";

interface ServiceCardProps {
    entity: ServiceType;
    actions?: {
        // Regular actions
        onOpen?: (entity: ServiceType) => void;
        onEdit?: (entity: ServiceType) => void;
        onDelete?: (entity: ServiceType) => void;
        // Selection actions for SelectableEntityTable
        onToggleSelection?: (entityId: number, isSelected: boolean) => void;
        isSelected?: (id: number) => boolean;
    };
    onRowClick?: (entity: ServiceType) => void;
}

export const ServiceCard: React.FC<ServiceCardProps> = ({
    entity: service,
    actions,
    onRowClick
}) => {
    const { t } = useTranslation();
    const isActive = service?.user_ids?.length > 0 && service?.inbound_ids?.length > 0;
    const isSelected = actions?.isSelected?.(service.id) ?? false;

    const handleCardClick = () => {
        if (actions?.onToggleSelection) {
            // If this is a selectable card, toggle selection on click
            actions.onToggleSelection(service.id, !isSelected);
        } else {
            // Otherwise, use the onRowClick
            onRowClick?.(service);
        }
    };

    return (
        <Card 
            className="h-full cursor-pointer hover:shadow-md transition-shadow"
            onClick={handleCardClick}
            data-testid={`card-service-${service.id}`}
        >
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                        {actions?.onToggleSelection && (
                            <Checkbox
                                checked={isSelected}
                                onCheckedChange={(checked) => {
                                    actions.onToggleSelection?.(service.id, !!checked);
                                }}
                                onClick={(e) => e.stopPropagation()}
                                aria-label={`Select ${service.name}`}
                                data-testid={`checkbox-service-${service.id}`}
                            />
                        )}
                        <div className={`w-3 h-3 rounded-full flex-shrink-0 ${
                            isActive ? 'bg-green-500' : 'bg-gray-400'
                        }`} />
                        <h3 className="font-semibold truncate" title={service.name}>
                            {service.name}
                        </h3>
                    </div>
                    <div className="text-xs text-muted-foreground">
                        {isActive ? t('active') : t('inactive')}
                    </div>
                </div>
            </CardHeader>
            
            <CardContent className="space-y-3 pt-0">
                <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                        <Icon name="Users" className="h-4 w-4 text-muted-foreground" />
                        <span>{t('users')}</span>
                    </div>
                    <span className="font-medium">{service?.user_ids?.length || 0}</span>
                </div>
                
                <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                        <Icon name="Router" className="h-4 w-4 text-muted-foreground" />
                        <span>{t('inbounds')}</span>
                    </div>
                    <span className="font-medium">{service?.inbound_ids?.length || 0}</span>
                </div>
                
                {actions && (actions.onOpen || actions.onEdit || actions.onDelete) && (
                    <div className="flex gap-1 pt-2 border-t">
                        {actions.onOpen && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    actions.onOpen?.(service);
                                }}
                                className="flex-1 h-8"
                                title={t('open')}
                                data-testid={`button-open-${service.id}`}
                            >
                                <Icon name="Eye" className="h-4 w-4" />
                            </Button>
                        )}
                        {actions.onEdit && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    actions.onEdit?.(service);
                                }}
                                className="flex-1 h-8"
                                title={t('edit')}
                                data-testid={`button-edit-${service.id}`}
                            >
                                <Icon name="Edit" className="h-4 w-4" />
                            </Button>
                        )}
                        {actions.onDelete && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    actions.onDelete?.(service);
                                }}
                                className="flex-1 h-8 hover:text-destructive"
                                title={t('delete')}
                                data-testid={`button-delete-${service.id}`}
                            >
                                <Icon name="Trash2" className="h-4 w-4" />
                            </Button>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
};