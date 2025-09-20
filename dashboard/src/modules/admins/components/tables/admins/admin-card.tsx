import * as React from 'react';
import {
    type AdminType,
    AdminEnabledPill,
    AdminPermissionPill,
} from "@wildosvpn/modules/admins";
import {
    Card,
    CardHeader,
    CardContent,
    CardFooter,
} from "@wildosvpn/common/components";
import i18n from "@wildosvpn/features/i18n";
import {
    DataTableActionsCell,
    type ColumnActions
} from "@wildosvpn/libs/entity-table";

interface AdminCardProps {
    entity: AdminType;
    actions: ColumnActions<AdminType>;
    onRowClick?: (entity: AdminType) => void;
}

export const AdminCard: React.FC<AdminCardProps> = ({ entity: admin, actions, onRowClick }) => {
    const handleCardClick = () => {
        onRowClick?.(admin);
    };

    const handleActionClick = (e: React.MouseEvent) => {
        e.stopPropagation();
    };

    return (
        <Card 
            className="w-full cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={handleCardClick}
            data-testid={`card-admin-${admin.username}`}
        >
            <CardHeader className="pb-3">
                {/* Header: Username + Permissions */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                        <span className="font-medium truncate" data-testid={`text-username-${admin.username}`}>
                            {admin.username}
                        </span>
                    </div>
                    <AdminPermissionPill admin={admin} />
                </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
                {/* Status and URL Prefix */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">
                            {i18n.t("status")}
                        </div>
                        <AdminEnabledPill admin={admin} />
                    </div>
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">
                            {i18n.t("url_prefix")}
                        </div>
                        <div className="text-sm" data-testid={`text-url-prefix-${admin.username}`}>
                            {admin?.subscription_url_prefix || (
                                <span className="text-muted-foreground">-</span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Usage Stats */}
                <div className="space-y-1">
                    <div className="text-sm font-medium text-muted-foreground">
                        {i18n.t("usage")}
                    </div>
                    <div className="text-sm text-muted-foreground" data-testid={`text-usage-${admin.username}`}>
                        {admin?.users_data_usage && admin.users_data_usage > 0 
                            ? `${admin.users_data_usage} users` 
                            : '-'
                        }
                    </div>
                </div>
            </CardContent>

            <CardFooter className="pt-2" onClick={handleActionClick}>
                {/* Action Menu */}
                <div className="flex items-center justify-end w-full">
                    <DataTableActionsCell 
                        {...actions} 
                        row={{ original: admin } as any}
                        className="w-auto justify-end"
                    />
                </div>
            </CardFooter>
        </Card>
    );
};