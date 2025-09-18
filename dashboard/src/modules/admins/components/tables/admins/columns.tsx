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
        accessorKey: "subscription_url_prefix",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("url_prefix")}
                column={column}
                className="hidden sm:table-cell"
            />
        ),
        cell: ({ row }) => {
            const admin = row.original;
            if (!admin?.subscription_url_prefix) return <span className="hidden sm:table-cell text-muted-foreground">-</span>;
            return <span className="hidden sm:table-cell text-sm">{admin.subscription_url_prefix}</span>;
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
        accessorKey: "enabled",
        enableSorting: false,
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("status")}
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
        accessorKey: "users_data_usage",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("usage")}
                column={column}
                className="hidden md:table-cell"
            />
        ),
        cell: ({ row }) => {
            const admin = row.original;
            const usage = admin?.users_data_usage || 0;
            return (
                <span className="hidden md:table-cell text-sm text-muted-foreground">
                    {usage > 0 ? `${usage} users` : '-'}
                </span>
            );
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
