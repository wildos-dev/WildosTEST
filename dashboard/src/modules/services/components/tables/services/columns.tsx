import { ColumnDef } from "@tanstack/react-table";
import { ServiceType } from "@wildosvpn/modules/services";
import {
    DataTableColumnHeader
} from "@wildosvpn/libs/entity-table"
import i18n from "@wildosvpn/features/i18n";
import {
    Button,
} from "@wildosvpn/common/components";
import { ColumnActions } from "@wildosvpn/libs/entity-table";
import { Icon } from "@wildosvpn/common/components/ui/icon";

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
            return (
                <div className="flex items-center gap-2">
                    <Icon name="Users" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                    <span>{service?.user_ids?.length || 0}</span>
                </div>
            );
        },
        meta: {
            className: "hidden sm:table-cell"
        }
    },
    {
        accessorKey: "inbounds",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('inbounds')} column={column} />,
        cell: ({ row }) => {
            const service = row.original;
            return (
                <div className="flex items-center gap-2">
                    <Icon name="Router" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                    <span>{service?.inbound_ids?.length || 0}</span>
                </div>
            );
        },
        meta: {
            className: "hidden md:table-cell"
        }
    },
    {
        accessorKey: "status",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('status')} column={column} />,
        cell: ({ row }) => {
            const service = row.original;
            const isActive = service?.user_ids?.length > 0 && service?.inbound_ids?.length > 0;
            return (
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                        isActive ? 'bg-green-500' : 'bg-gray-400'
                    }`} />
                    <span className="text-sm">
                        {isActive ? i18n.t('active') : i18n.t('inactive')}
                    </span>
                </div>
            );
        },
        meta: {
            className: "hidden lg:table-cell"
        }
    },
    {
        id: "actions",
        cell: ({ row }) => {
            return (
                <div className="flex gap-1 sm:gap-2 opacity-100 sm:opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                    <Button
                        variant="ghost"
                        size="touch-sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            actions.onOpen(row.original);
                        }}
                        className="focus-visible:opacity-100"
                        title={i18n.t('open')}
                    >
                        <Icon name="Eye" className="h-4 w-4 sm:h-5 sm:w-5" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="touch-sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            actions.onEdit(row.original);
                        }}
                        className="focus-visible:opacity-100"
                        title={i18n.t('edit')}
                    >
                        <Icon name="Edit" className="h-4 w-4 sm:h-5 sm:w-5" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="touch-sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            actions.onDelete(row.original);
                        }}
                        className="focus-visible:opacity-100 hover:text-destructive"
                        title={i18n.t('delete')}
                    >
                        <Icon name="Trash2" className="h-4 w-4 sm:h-5 sm:w-5" />
                    </Button>
                </div>
            );
        },
    }
]);

// Add hover effect to table rows
export const tableRowClassName = "group hover:bg-muted/50 cursor-pointer transition-colors";