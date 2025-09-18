import { ColumnDef } from "@tanstack/react-table"
import { DataTableColumnHeader } from "@wildosvpn/libs/entity-table"
import i18n from "@wildosvpn/features/i18n"
import {
    UserType,
    UserActivatedPill,
    UserUsedTraffic,
    UserExpirationValue,
    userTrafficSortingFn,
} from "@wildosvpn/modules/users"
import { Icon } from "@wildosvpn/common/components/ui/icon"

export const columns: ColumnDef<UserType>[] = [
    {
        accessorKey: "username",
        header: ({ column }) => <DataTableColumnHeader title={i18n.t('username')} column={column} />,
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
                <Icon name="User" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                <span className="font-medium">{row.original.username}</span>
            </div>
        ),
    },
    {
        accessorKey: "activated",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("activated")}
                column={column}
            />
        ),
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
                <Icon name="Power" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                <UserActivatedPill user={row.original} />
            </div>
        ),
        meta: {
            className: "hidden sm:table-cell"
        }
    },
    {
        accessorKey: "used_traffic",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("page.users.used_traffic")}
                column={column}
            />
        ),
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
                <Icon name="BarChart3" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                <UserUsedTraffic user={row.original} />
            </div>
        ),
        sortingFn: (rowA, rowB) => userTrafficSortingFn(rowA.original, rowB.original),
        meta: {
            className: "hidden md:table-cell"
        }
    },
    {
        accessorKey: "expire",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("page.users.expire_date")}
                column={column}
            />
        ),
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
                <Icon name="Calendar" className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                <UserExpirationValue user={row.original} />
            </div>
        ),
        meta: {
            className: "hidden lg:table-cell"
        }
    },
];
