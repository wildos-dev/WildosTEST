import * as React from 'react';
import { InboundType } from "@wildosvpn/modules/inbounds";
import { Card, CardContent, CardHeader, Badge, Checkbox } from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { useTranslation } from "react-i18next";

interface InboundCardProps {
    entity: InboundType;
    actions?: {
        onToggleSelection?: (entityId: number, isSelected: boolean) => void;
        isSelected?: (id: number) => boolean;
    };
    onRowClick?: (entity: InboundType) => void;
}

export const InboundCard: React.FC<InboundCardProps> = ({
    entity: inbound,
    actions,
    onRowClick
}) => {
    const { t } = useTranslation();
    const isSelected = actions?.isSelected?.(inbound.id) ?? false;

    const handleCardClick = () => {
        if (actions?.onToggleSelection) {
            // If this is a selectable card, toggle selection on click
            actions.onToggleSelection(inbound.id, !isSelected);
        } else {
            // Otherwise, use the onRowClick
            onRowClick?.(inbound);
        }
    };

    return (
        <Card 
            className="h-full cursor-pointer hover:shadow-md transition-shadow"
            onClick={handleCardClick}
            data-testid={`card-inbound-${inbound.id}`}
        >
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                        {actions?.onToggleSelection && (
                            <Checkbox
                                checked={isSelected}
                                onCheckedChange={(checked) => {
                                    actions.onToggleSelection?.(inbound.id, !!checked);
                                }}
                                onClick={(e) => e.stopPropagation()}
                                aria-label={`Select ${inbound.tag}`}
                                data-testid={`checkbox-inbound-${inbound.id}`}
                            />
                        )}
                        <Icon name="Router" className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                        <h3 className="font-semibold truncate" title={inbound.tag}>
                            {inbound.tag}
                        </h3>
                    </div>
                </div>
            </CardHeader>
            
            <CardContent className="space-y-3 pt-0">
                <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                        <Icon name="Shield" className="h-4 w-4 text-muted-foreground" />
                        <span>{t('protocol')}</span>
                    </div>
                    <Badge className="py-1 px-2">{inbound.protocol}</Badge>
                </div>
                
                <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                        <Icon name="Server" className="h-4 w-4 text-muted-foreground" />
                        <span>{t('nodes')}</span>
                    </div>
                    <Badge className="py-1 px-2">{inbound.node.name}</Badge>
                </div>
            </CardContent>
        </Card>
    );
};