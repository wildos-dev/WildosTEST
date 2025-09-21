import * as React from 'react';
import { Button } from "@wildosvpn/common/components";
import { SelectableEntityTable, useRowSelection } from "@wildosvpn/libs/entity-table";
import { columns } from "./columns";
import { type ServiceType, useServicesUpdateMutation, fetchSelectableServiceInbounds } from "@wildosvpn/modules/services";
import { useTranslation } from "react-i18next";
import { InboundCard } from "./inbound-card";

interface ServiceInboundsTableProps {
    service: ServiceType;
}

export const ServiceInboundsTable: React.FC<ServiceInboundsTableProps> = ({
    service,
}) => {
    const { mutate: updateService } = useServicesUpdateMutation();
    const { selectedRow, setSelectedRow } =
        useRowSelection(Object.fromEntries(service.inbound_ids.map(entityId => [String(entityId), true])));
    const [selectedInbound, setSelectedInbound] = React.useState<number[]>(service.inbound_ids);
    const { t } = useTranslation();

    const handleApply = React.useCallback(() => {
        updateService({ id: service.id, name: service.name, inbound_ids: selectedInbound });
    }, [selectedInbound, service, updateService]);

    const disabled = selectedInbound.length < 1;

    const handleToggleSelection = (entityId: number, isSelected: boolean) => {
        setSelectedInbound(prev => 
            isSelected 
                ? [...new Set([...prev, entityId])]  // Add if not already present
                : prev.filter(id => id !== entityId)  // Remove if present
        );
    };

    const isInboundSelected = (id: number) => {
        return selectedInbound.includes(id);
    };

    return (
        <div className="flex flex-col gap-4 p-4 sm:p-6">
            <SelectableEntityTable
                columns={columns}
                entityKey="inbounds"
                parentEntityKey="services"
                parentEntityId={service.id}
                existingEntityIds={service.inbound_ids}
                fetchEntity={fetchSelectableServiceInbounds}
                primaryFilter="tag"
                rowSelection={{ selectedRow: selectedRow, setSelectedRow: setSelectedRow }}
                entitySelection={{ selectedEntity: selectedInbound, setSelectedEntity: setSelectedInbound }}
                CardComponent={InboundCard}
                cardActions={{ 
                    onToggleSelection: handleToggleSelection,
                    isSelected: isInboundSelected
                }}
            />

            <Button 
                onClick={handleApply} 
                disabled={disabled}
                className="w-full sm:w-auto h-12 sm:h-10 font-semibold"
            >
                {t("apply")}
            </Button>
        </div>
    );
};
