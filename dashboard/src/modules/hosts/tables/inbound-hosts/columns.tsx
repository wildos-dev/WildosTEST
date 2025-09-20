import { ColumnDef } from "@tanstack/react-table"
import { HostType } from "@wildosvpn/modules/hosts"
import {
    DataTableColumnHeader
} from "@wildosvpn/libs/entity-table"
import i18n from "@wildosvpn/features/i18n"
import {
    type ColumnActions
} from "@wildosvpn/libs/entity-table";
import {
    Badge,
    Button
} from "@wildosvpn/common/components"
import { Icon } from "@wildosvpn/common/components/ui/icon"

export const columns = (actions: ColumnActions<HostType>): ColumnDef<HostType>[] => ([
    {
        accessorKey: "remark",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('name')} column={column} />,
        cell: ({ row }) => {
            const host = row.original;
            return (
                <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{host.remark}</span>
                </div>
            );
        },
    },
    {
        accessorKey: "address",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('address')} column={column} />,
        cell: ({ row }) => {
            const host = row.original;
            return (
                <div className="hidden lg:block text-sm text-muted-foreground truncate">
                    {host.address}:{host.port}
                </div>
            );
        },
    },
    {
        id: "type",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('type')} column={column} />,
        cell: () => {
            return (
                <div className="hidden md:block">
                    <Badge variant="outline" className="text-xs">
                        {'TCP'}
                    </Badge>
                </div>
            );
        },
    },
    {
        id: "inbound",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('inbound')} column={column} />,
        cell: () => {
            return (
                <div className="hidden sm:block">
                    <Badge variant="secondary" className="text-xs">
                        {i18n.t('inbound')}
                    </Badge>
                </div>
            );
        },
    },
    {
        id: "status",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('status')} column={column} />,
        cell: ({ row }) => {
            const host = row.original;
            const isActive = !host.is_disabled;
            return (
                <Badge 
                    variant={isActive ? "default" : "secondary"} 
                    className="text-xs"
                >
                    {isActive ? i18n.t('active') : i18n.t('disabled')}
                </Badge>
            );
        },
    },
    {
        id: "actions",
        cell: ({ row }) => {
            return (
                <div className="relative group">
                    <div className="absolute top-2 right-2 sm:top-3 sm:right-3 flex gap-1 sm:gap-2 opacity-100 sm:opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity z-20">
                        <Button
                            variant="secondary"
                            size="touch-sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                actions.onEdit?.(row.original);
                            }}
                            className="focus-visible:opacity-100 shadow-lg"
                            title={i18n.t('edit')}
                        >
                            <Icon name="Edit" className="h-4 w-4 sm:h-5 sm:w-5" />
                        </Button>
                        <Button
                            variant="destructive" 
                            size="touch-sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                actions.onDelete?.(row.original);
                            }}
                            className="focus-visible:opacity-100 shadow-lg"
                            title={i18n.t('delete')}
                        >
                            <Icon name="Trash2" className="h-4 w-4 sm:h-5 sm:w-5" />
                        </Button>
                    </div>
                </div>
            );
        },
    }
]);
