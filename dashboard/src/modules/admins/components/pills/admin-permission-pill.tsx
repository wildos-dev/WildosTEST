import * as React from "react";
import { BooleanPill } from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { AdminProp } from "@wildosvpn/modules/admins";

export const AdminPermissionPill: React.FC<AdminProp> = ({ admin }) => {
    const { t } = useTranslation();
    return (
        <BooleanPill
            active={admin.is_sudo}
            activeLabel={t('sudo')}
            activeVariant="royal"
            inactiveLabel={t('normal')}
            inactiveVariant="warning"
        />
    )
}
