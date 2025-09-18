import * as React from 'react';
import { Button, HStack } from "@wildosvpn/common/components";
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import { useTranslation } from "react-i18next";
import { getSubscriptionLink } from "@wildosvpn/common/utils";
import { useUserSubscriptionRevokeCmd } from "@wildosvpn/modules/users";
import { CopyToClipboardButton } from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import type { QRCodeProps } from "./qrcode";

export const SubscriptionActions: React.FC<QRCodeProps> = ({ entity }) => {
    const subscribeQrLink = getSubscriptionLink(entity.subscription_url);
    const { mutate: revokeSubscription } = useUserSubscriptionRevokeCmd();
    const { t } = useTranslation();
    const isMobile = !useScreenBreakpoint('md');

    return (
        <div className={`w-full ${isMobile ? 'space-y-3' : ''}`}>
            {isMobile ? (
                // Mobile: Stack vertically with full width buttons for better touch targets
                <div className="space-y-3">
                    <CopyToClipboardButton
                        text={subscribeQrLink}
                        successMessage={t("page.users.settings.subscription_link.copied")}
                        copyLabel={t("page.users.settings.subscription_link.copy")}
                        errorLabel={t("page.users.settings.subscription_link.error")}
                        copyIcon={(props: any) => <Icon name="SquareCode" {...props} />}
                        className="w-full h-12 text-base"
                        data-testid="button-copy-subscription"
                    />
                    <Button 
                        variant="destructive" 
                        className="w-full h-12 text-base" 
                        onClick={() => revokeSubscription(entity)}
                        data-testid="button-revoke-subscription"
                    >
                        {t("page.users.revoke_subscription")}
                    </Button>
                </div>
            ) : (
                // Desktop: Side by side layout
                <HStack className="w-full items-center my-2 gap-3">
                    <CopyToClipboardButton
                        text={subscribeQrLink}
                        successMessage={t("page.users.settings.subscription_link.copied")}
                        copyLabel={t("page.users.settings.subscription_link.copy")}
                        errorLabel={t("page.users.settings.subscription_link.error")}
                        copyIcon={(props: any) => <Icon name="SquareCode" {...props} />}
                        className="flex-1"
                        data-testid="button-copy-subscription"
                    />
                    <Button 
                        variant="destructive" 
                        className="flex-1" 
                        onClick={() => revokeSubscription(entity)}
                        data-testid="button-revoke-subscription"
                    >
                        {t("page.users.revoke_subscription")}
                    </Button>
                </HStack>
            )}
        </div>
    );
};
