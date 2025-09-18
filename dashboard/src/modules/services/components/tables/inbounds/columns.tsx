
import { ColumnDef } from "@tanstack/react-table"
import { InboundType } from "@wildosvpn/modules/inbounds"
import {
    DataTableColumnHeader
} from "@wildosvpn/libs/entity-table"
import i18n from "@wildosvpn/features/i18n"
import { Badge, Checkbox } from "@wildosvpn/common/components"
import { Icon } from "@wildosvpn/common/components/ui/icon"

export const columns: ColumnDef<InboundType>[] = [
    {
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={
                    table.getIsAllPageRowsSelected() ||
                    (table.getIsSomePageRowsSelected() && "indeterminate")
                }
                onCheckedChange={(value) => {
                    table.toggleAllPageRowsSelected(!!value)
                }}
                aria-label="Select all"
            />
        ),
        cell: ({ row }) => (
            <Checkbox
                checked={row.getIsSelected()}
                onCheckedChange={(value) => row.toggleSelected(!!value)}
                aria-label="Select row"
            />
        ),
        enableSorting: false,
        enableHiding: false,
    },
    {
        accessorKey: "tag",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('tag')} column={column} />,
    },
    {
        accessorKey: 'protocol',
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('protocol')} column={column} />,
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
                <Icon name="Shield" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                <Badge className="py-1 px-2">{row.original.protocol}</Badge>
            </div>
        ),
        meta: {
            className: "hidden sm:table-cell"
        }
    },
    {
        accessorKey: 'node',
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('nodes')} column={column} />,
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
                <Icon name="Server" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                <Badge className="py-1 px-2">{row.original.node.name}</Badge>
            </div>
        ),
        meta: {
            className: "hidden md:table-cell"
        }
    }
];
