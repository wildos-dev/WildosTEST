import * as React from 'react';
import {
    type UserType,
    OnlineStatus,
    UserUsedTraffic,
    UserActivatedPill,
    UserExpireStrategyPill,
    UserExpirationValue
} from "@wildosvpn/modules/users";
import i18n from "@wildosvpn/features/i18n";
import {
    CopyToClipboardButton,
    buttonVariants,
    Card,
    CardHeader,
    CardContent,
    CardFooter,
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { getSubscriptionLink } from "@wildosvpn/common/utils";
import { useAuth } from "@wildosvpn/modules/auth";
import {
    DataTableActionsCell,
    type ColumnActions
} from "@wildosvpn/libs/entity-table";

interface UserCardProps {
    entity: UserType;
    actions: ColumnActions<UserType>;
    onRowClick?: (entity: UserType) => void;
}

export const UserCard: React.FC<UserCardProps> = ({ entity: user, actions, onRowClick }) => {
    const { isSudo } = useAuth();
    
    const handleCardClick = () => {
        onRowClick?.(user);
    };

    const handleActionClick = (e: React.MouseEvent) => {
        e.stopPropagation();
    };

    return (
        <Card 
            className="w-full cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={handleCardClick}
            data-testid={`card-user-${user.username}`}
        >
            <CardHeader className="pb-3">
                {/* Header: Username + Status + Activation */}
                <div className="flex items-center justify-between">
                    <div className="flex flex-row gap-2 items-center min-w-0 flex-1">
                        <OnlineStatus user={user} />
                        <span className="font-medium truncate" data-testid={`text-username-${user.username}`}>
                            {user.username || i18n.t("unknown")}
                        </span>
                    </div>
                    <UserActivatedPill user={user} />
                </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
                {/* Traffic Usage with Progress */}
                <div className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">
                        {i18n.t("page.users.used_traffic")}
                    </div>
                    <UserUsedTraffic user={user} />
                </div>

                {/* Expiration Strategy and Date */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">
                            {i18n.t("page.users.expire_method")}
                        </div>
                        <UserExpireStrategyPill user={user} />
                    </div>
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">
                            {i18n.t("page.users.expire_date")}
                        </div>
                        <UserExpirationValue user={user} />
                    </div>
                </div>

                {/* Owner (for sudo users only) */}
                {isSudo() && (user as any).owner_username && (
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">
                            {i18n.t("owner")}
                        </div>
                        <div className="text-sm" data-testid={`text-owner-${user.username}`}>
                            {(user as any).owner_username}
                        </div>
                    </div>
                )}
            </CardContent>

            <CardFooter className="pt-2" onClick={handleActionClick}>
                {/* Action Buttons */}
                <div className="flex items-center gap-2 w-full">
                    <CopyToClipboardButton
                        text={getSubscriptionLink(user.subscription_url || '')}
                        successMessage={i18n.t(
                            "page.users.settings.subscription_link.copied",
                        )}
                        copyIcon={(props: any) => <Icon name="Link" {...props} />}
                        className={buttonVariants({
                            variant: "secondary",
                            size: "touch-sm",
                            className: "size-11 min-w-11",
                        })}
                        tooltipMsg={i18n.t("page.users.settings.subscription_link.copy")}
                        data-testid={`button-copy-link-${user.username}`}
                    />
                    <div className="flex-1">
                        <DataTableActionsCell 
                            {...actions} 
                            row={{ original: user } as any}
                            className="w-full justify-end"
                        />
                    </div>
                </div>
            </CardFooter>
        </Card>
    );
};