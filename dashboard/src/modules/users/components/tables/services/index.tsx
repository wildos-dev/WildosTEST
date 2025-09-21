
import * as React from 'react';
import { Button } from "@wildosvpn/common/components";
import { SelectableEntityTable, useRowSelection } from "@wildosvpn/libs/entity-table";
import { columns } from "./columns";
import {
    type UserType,
    useUsersUpdateMutation,
} from "@wildosvpn/modules/users";
import { useTranslation } from "react-i18next";
import { fetchUserServices } from "@wildosvpn/modules/services";
import { ServiceCard } from "@wildosvpn/modules/services/components/tables/services/service-card";

interface UserServicesTableProps {
    user: UserType;
}

export const UserServicesTable: React.FC<UserServicesTableProps> = ({ user }) => {
    const { mutate: updateUser } = useUsersUpdateMutation();
    const { selectedRow, setSelectedRow } =
        useRowSelection(
            Object.fromEntries(
                user.service_ids.map(entityId => [String(entityId), true])
            )
        );
    const [selectedService, setSelectedService] = React.useState<number[]>(user.service_ids);
    const { t } = useTranslation();

    const handleApply = React.useCallback(() => {
        updateUser({ ...user, service_ids: selectedService });
    }, [selectedService, user, updateUser]);

    const handleToggleSelection = (entityId: number, isSelected: boolean) => {
        setSelectedService(prev => 
            isSelected 
                ? [...new Set([...prev, entityId])]  // Add if not already present
                : prev.filter(id => id !== entityId)  // Remove if present
        );
    };

    const isServiceSelected = (id: number) => {
        return selectedService.includes(id);
    };

    return (
        <div className="flex flex-col gap-4">
            <SelectableEntityTable
                fetchEntity={fetchUserServices}
                columns={columns}
                primaryFilter="name"
                existingEntityIds={user.service_ids}
                entityKey="services"
                parentEntityKey="users"
                parentEntityId={user.username}
                rowSelection={{ selectedRow: selectedRow, setSelectedRow: setSelectedRow }}
                entitySelection={{ selectedEntity: selectedService, setSelectedEntity: setSelectedService }}
                CardComponent={ServiceCard}
                cardActions={{ 
                    onToggleSelection: handleToggleSelection,
                    isSelected: isServiceSelected
                }}
            />

            <Button onClick={handleApply} disabled={selectedService.length === 0}>
                {t("apply")}
            </Button>
        </div>
    );
};
