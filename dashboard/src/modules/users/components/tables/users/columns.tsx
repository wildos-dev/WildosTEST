import {
    type UserType,
    OnlineStatus,
    UserUsedTraffic,
    UserActivatedPill,
    UserExpireStrategyPill,
    UserExpirationValue
} from "@wildosvpn/modules/users";
import { useAdminsQuery } from "@wildosvpn/modules/admins";
import i18n from "@wildosvpn/features/i18n";
import {
    CopyToClipboardButton,
    buttonVariants,
    NoPropogationButton,
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { getSubscriptionLink } from "@wildosvpn/common/utils";
import {
    DataTableColumnHeader,
    DataTableColumnHeaderFilterOption,
    DataTableActionsCell,
    type ColumnActions, type ColumnDefWithSudoRole
} from "@wildosvpn/libs/entity-table";
import { type Column } from "@tanstack/react-table";

export const columns = (actions: ColumnActions<UserType>): ColumnDefWithSudoRole<UserType>[] => [
    {
        accessorKey: "username",
        header: ({ column }) => (
            <DataTableColumnHeader title={i18n.t("username")} column={column} />
        ),
        cell: ({ row }) => {
            const user = row.original;
            if (!user) return null;
            
            return (
                <div className="flex flex-row gap-2 items-center">
                    <OnlineStatus user={user} /> {user.username || i18n.t("unknown")}
                </div>
            );
        },
    },
    {
        accessorKey: "activated",
        enableSorting: false,
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("activated")}
                column={column}
            />
        ),
        cell: ({ row }) => {
            const user = row.original;
            if (!user) return null;
            return <UserActivatedPill user={user} />;
        },
    },
    {
        accessorKey: "owner_username",
        enableSorting: false,
        sudoVisibleOnly: true,
        header: ({ column }) => <AdminsColumnsHeaderOptionFilter column={column} />,
    },
    {
        accessorKey: "used_traffic",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("page.users.used_traffic")}
                column={column}
            />
        ),
        cell: ({ row }) => {
            const user = row.original;
            if (!user) return null;
            return <UserUsedTraffic user={user} />;
        },
    },
    {
        accessorKey: "expire_strategy",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("page.users.expire_method")}
                column={column}
            />
        ),
        cell: ({ row }) => {
            const user = row.original;
            if (!user) return null;
            return <UserExpireStrategyPill user={user} />;
        },
        enableSorting: false,
    },
    {
        accessorKey: "expire_date",
        header: ({ column }) => (
            <DataTableColumnHeader
                title={i18n.t("page.users.expire_date")}
                column={column}
            />
        ),
        cell: ({ row }) => {
            const user = row.original;
            if (!user) return null;
            return <UserExpirationValue user={user} />;
        },
    },
    {
        id: "actions",
        cell: ({ row }) => {
            const user = row.original;
            if (!user) return null;
            
            return (
                <NoPropogationButton row={row} actions={actions}>
                    <CopyToClipboardButton
                        text={getSubscriptionLink(user.subscription_url || '')}
                        successMessage={i18n.t(
                            "page.users.settings.subscription_link.copied",
                        )}
                        copyIcon={(props: any) => <Icon name="Link" {...props} />}
                        className={buttonVariants({
                            variant: "secondary",
                            className: "size-8",
                        })}
                        tooltipMsg={i18n.t("page.users.settings.subscription_link.copy")}
                    />
                    <DataTableActionsCell {...actions} row={row} />
                </NoPropogationButton>
            );
        }
    }
];

function AdminsColumnsHeaderOptionFilter<TData, TValue>({ column }: { column: Column<TData, TValue> }) {
    const { data } = useAdminsQuery({ page: 1, size: 100, filters: {} });
    return (
        <DataTableColumnHeaderFilterOption
            title={i18n.t("owner")}
            column={column}
            options={data?.entities?.map((admin) => admin?.username).filter(Boolean) || []}
        />
    );
}

