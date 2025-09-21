import * as React from 'react';
import {
    ServicesQueryFetchKey,
    fetchServices,
    ServiceType
} from "@wildosvpn/modules/services";
import { columns as columnsFn } from "./columns";
import { EntityTable } from "@wildosvpn/libs/entity-table";
import { useNavigate } from "@tanstack/react-router";
import { ServiceCard } from "./service-card";

export const ServicesTable: React.FC = () => {
    const navigate = useNavigate({ from: "/services" });
    const onEdit = (entity: ServiceType) => {
        navigate({
            to: "/services/$serviceId/edit",
            params: { serviceId: String(entity.id) },
        })
    }

    const onDelete = (entity: ServiceType) => {
        navigate({
            to: "/services/$serviceId/delete",
            params: { serviceId: String(entity.id) },
        })
    }

    const onOpen = (entity: ServiceType) => {
        navigate({
            to: "/services/$serviceId",
            params: { serviceId: String(entity.id) },
        })
    }

    const columns = columnsFn({ onEdit, onDelete, onOpen });
    const cardActions = { onEdit, onDelete, onOpen };

    return (
        <EntityTable
            fetchEntity={fetchServices}
            columns={columns}
            primaryFilter="name"
            entityKey={ServicesQueryFetchKey}
            onCreate={() => navigate({ to: "/services/create" })}
            onOpen={onOpen}
            CardComponent={ServiceCard}
            cardActions={cardActions}
        />
    );
};
