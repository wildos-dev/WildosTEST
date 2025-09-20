import * as React from "react";
import { BooleanPill } from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { AdminProp } from "@wildosvpn/modules/admins";

export const AdminEnabledPill: React.FC<AdminProp> = ({ admin }) => {
    const { t } = useTranslation();
    return (
        <BooleanPill
            active={admin.enabled}
            activeLabel={t('enabled')}
            inactiveLabel={t('disabled')}
        />
    )
}
