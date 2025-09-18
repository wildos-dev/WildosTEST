import type { ColumnDef } from "@tanstack/react-table";
import {
    type AdminType,
    AdminEnabledPill,
    AdminPermissionPill,
} from "@wildosvpn/modules/admins";
import {
    DataTableActionsCell,
    DataTableColumnHeader
} from "@wildosvpn/libs/entity-table"
import i18n from "@wildosvpn/features/i18n";
import {
    NoPropogationButton,
} from "@wildosvpn/common/components";
import {
    type ColumnActions
} from "@wildosvpn/libs/entity-table";

export const columns = (actions: ColumnActions<AdminType>): ColumnDef<AdminType, any>[] => [
    {
        accessorKey: "username",
        header: ({ column }) => (
            <DataTableColumnHeader title={i18n.t("username")} column={column} />
        ),
    },
    {
        accessorKey: "enabled",
        enableSorting: false,
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("enabled")}
                column={column}
            />
        ),
        cell: ({ row }) => {
            const admin = row.original;
            if (!admin) return null;
            return <AdminEnabledPill admin={admin} />;
        },
    },
    {
        accessorKey: "is_sudo",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("page.admins.permission")}
                column={column}
            />
        ),
        cell: ({ row }) => {
            const admin = row.original;
            if (!admin) return null;
            return <AdminPermissionPill admin={admin} />;
        },
    },
    {
        id: "actions",
        cell: ({ row }) => (
            <NoPropogationButton row={row} actions={actions}>
                <DataTableActionsCell {...actions} row={row} />
            </NoPropogationButton>
        ),
    }
];
