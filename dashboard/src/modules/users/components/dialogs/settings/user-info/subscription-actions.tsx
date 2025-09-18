import * as React from 'react';
import { Button, HStack } from "@wildosvpn/common/components";
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
    return (
        <HStack className="w-full items-center my-2">
            <CopyToClipboardButton
                text={subscribeQrLink}
                successMessage={t("page.users.settings.subscription_link.copied")}
                copyLabel={t("page.users.settings.subscription_link.copy")}
                errorLabel={t("page.users.settings.subscription_link.error")}
                copyIcon={(props: any) => <Icon name="SquareCode" {...props} />}
                className="w-1/2"
            />
            <Button variant="destructive" className="w-1/2" onClick={() => revokeSubscription(entity)}>
                {t("page.users.revoke_subscription")}
            </Button>
        </HStack>
    );
};
