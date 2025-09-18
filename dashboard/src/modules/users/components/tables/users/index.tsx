import * as React from 'react';
import { fetchUsers, UserType, UsersQueryFetchKey } from "@wildosvpn/modules/users";
import { columns as columnsFn } from "./columns";
import { EntityTable } from "@wildosvpn/libs/entity-table";
import { useAuth } from "@wildosvpn/modules/auth";
import { useNavigate } from "@tanstack/react-router";

export const UsersTable: React.FC = () => {
    const navigate = useNavigate({ from: "/users" });
    const { isSudo } = useAuth();

    const onOpen = (entity: UserType) => {
        navigate({
            to: "/users/$userId",
            params: { userId: entity.username },
        })
    }

    const onEdit = (entity: UserType) => {
        navigate({
            to: "/users/$userId/edit",
            params: { userId: entity.username },
        })
    }

    const onDelete = (entity: UserType) => {
        navigate({
            to: "/users/$userId/delete",
            params: { userId: entity.username },
        })
    }

    const columns = columnsFn({ onEdit, onDelete, onOpen });
    const noneSudoColumns = columns.filter((column) => !column.sudoVisibleOnly);

    return (
        <EntityTable
            fetchEntity={fetchUsers}
            columns={isSudo() ? columns : noneSudoColumns}
            primaryFilter="username"
            entityKey={UsersQueryFetchKey}
            onCreate={() => navigate({ to: "/users/create" })}
            onOpen={onOpen}
        />
    );
};
