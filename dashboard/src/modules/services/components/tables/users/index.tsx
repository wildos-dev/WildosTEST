
import * as React from "react";
import { DoubleEntityTable } from "@wildosvpn/libs/entity-table";
import { columns } from "./columns";
import { fetchServiceUsers, type ServiceType } from "@wildosvpn/modules/services";

interface ServicesUsersTableProps {
    service: ServiceType
}

export const ServicesUsersTable: React.FC<ServicesUsersTableProps> = ({ service }) => {

    return (
        <div className="p-4 sm:p-6">
            <DoubleEntityTable
                columns={columns}
                entityId={service.id}
                fetchEntity={fetchServiceUsers}
                primaryFilter="username"
                entityKey='services'
            />
        </div>
    )
}
