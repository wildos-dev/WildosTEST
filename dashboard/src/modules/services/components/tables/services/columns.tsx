import { ColumnDef } from "@tanstack/react-table";
import { ServiceType } from "@wildosvpn/modules/services";
import {
    DataTableActionsCell,
    DataTableColumnHeader
} from "@wildosvpn/libs/entity-table"
import i18n from "@wildosvpn/features/i18n";
import {
    NoPropogationButton,
} from "@wildosvpn/common/components";
import { ColumnActions } from "@wildosvpn/libs/entity-table";

export const columns = (actions: ColumnActions<ServiceType>): ColumnDef<ServiceType>[] => ([
    {
        accessorKey: "name",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('name')} column={column} />,
    },
    {
        accessorKey: "users",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('users')} column={column} />,
        cell: ({ row }) => {
            const service = row.original;
            return `${service?.user_ids?.length || 0}`;
        }
    },
    {
        accessorKey: "inbounds",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('inbounds')} column={column} />,
        cell: ({ row }) => {
            const service = row.original;
            return `${service?.inbound_ids?.length || 0}`;
        }
    },
    {
        id: "actions",
        cell: ({ row }) => {
            return (
                <NoPropogationButton row={row} actions={actions}>
                    <DataTableActionsCell {...actions} row={row} />
                </NoPropogationButton>
            );
        },
    }
]);
