import * as React from 'react';
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
    Awaiting,
    SettingsInfoSkeleton,
    SettingsDialogProps,
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@wildosvpn/common/components";
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import {
    UserServicesTable,
    UserNodesUsageWidget,
    type UserType,
} from "@wildosvpn/modules/users";
import { useTranslation } from "react-i18next";
import {
    SubscriptionActions,
    QRCodeSection,
    UserInfoTable,
} from "./user-info";

interface UsersSettingsDialogProps extends SettingsDialogProps {
    entity: UserType | null;
    onClose: () => void;
    isPending: boolean;
}

export const UsersSettingsDialog: React.FC<UsersSettingsDialogProps> = ({
    onOpenChange,
    open,
    entity,
    isPending,
}) => {
    const { t } = useTranslation();
    const isMobile = !useScreenBreakpoint('md');

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className={`max-w-4xl max-h-[95vh] ${isMobile ? 'h-screen max-w-full' : ''}`}>
                <DialogHeader>
                    <DialogTitle>
                        {entity ? `${entity.username} - ${t("page.users.settings.title")}` : t("page.users.settings.title")}
                    </DialogTitle>
                </DialogHeader>
            <Awaiting
                Component={
                    entity ? (
                        <div className="flex flex-col h-full overflow-hidden">
                            <Tabs defaultValue="info" className="w-full h-full flex flex-col">
                                <TabsList className={`w-full bg-accent shrink-0 ${
                                    isMobile 
                                        ? "grid grid-cols-2 h-auto gap-1 p-1" 
                                        : "grid grid-cols-4"
                                }`}>
                                    <TabsTrigger 
                                        className="w-full text-xs sm:text-sm px-2 py-2" 
                                        value="info"
                                        data-testid="tab-user-info"
                                    >
                                        {t("user_info")}
                                    </TabsTrigger>
                                    <TabsTrigger 
                                        className="w-full text-xs sm:text-sm px-2 py-2" 
                                        value="services"
                                        data-testid="tab-services"
                                    >
                                        {t("services")}
                                    </TabsTrigger>
                                    <TabsTrigger 
                                        className="w-full text-xs sm:text-sm px-2 py-2" 
                                        value="subscription"
                                        data-testid="tab-subscription"
                                    >
                                        {t("subscription")}
                                    </TabsTrigger>
                                    <TabsTrigger 
                                        className="w-full text-xs sm:text-sm px-2 py-2" 
                                        value="nodes-usage"
                                        data-testid="tab-nodes-usage"
                                    >
                                        {isMobile ? t("usage") : t("page.users.nodes-usage")}
                                    </TabsTrigger>
                                </TabsList>
                                
                                <div className="flex-1 overflow-y-auto">
                                    <TabsContent
                                        value="info"
                                        className="flex flex-col gap-4 w-full h-full p-4 space-y-0"
                                    >
                                        <UserInfoTable user={entity} />
                                    </TabsContent>
                                    <TabsContent value="services" className="p-4 space-y-0">
                                        <UserServicesTable user={entity} />
                                    </TabsContent>
                                    <TabsContent value="subscription" className="p-4 space-y-6">
                                        <QRCodeSection entity={entity} />
                                        <SubscriptionActions entity={entity} />
                                    </TabsContent>
                                    <TabsContent value="nodes-usage" className="p-4 space-y-0">
                                        <UserNodesUsageWidget user={entity} />
                                    </TabsContent>
                                </div>
                            </Tabs>
                        </div>
                    ) : (
                        <div className="text-center py-8">{t('not-found.user')}</div>
                    )
                }
                Skeleton={<SettingsInfoSkeleton />}
                isFetching={isPending}
            />
            </DialogContent>
        </Dialog>
    );
};
