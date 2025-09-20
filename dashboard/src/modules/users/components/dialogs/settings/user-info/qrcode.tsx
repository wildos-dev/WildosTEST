import * as React from 'react';
import type { UserType } from "@wildosvpn/modules/users";
import QRCode from "react-qr-code";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { getSubscriptionLink } from "@wildosvpn/common/utils";

export interface QRCodeProps {
    entity: UserType;
}

export const QRCodeSection: React.FC<QRCodeProps> = ({ entity }) => {
    const subscribeQrLink = getSubscriptionLink(entity.subscription_url);
    const { t } = useTranslation();
    return (
        <Card>
            <CardHeader className="flex flex-row justify-between items-center w-full">
                <CardTitle className="flex flex-row gap-4 justify-start">
                    <Icon name="QrCode" />
                    {t("subscription")} QRCode
                </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col justify-center items-center py-10 w-full h-full">
                <QRCode size={150} className="size-2/3 bg-white p-4" value={subscribeQrLink} />
            </CardContent>
        </Card>
    );
};
