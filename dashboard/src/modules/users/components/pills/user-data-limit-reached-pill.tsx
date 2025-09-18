import * as React from 'react';
import { BooleanPill } from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { UserProp } from "@wildosvpn/modules/users";

export const UserDataLimitReachedPill: React.FC<UserProp> = ({ user }) => {
    const { t } = useTranslation();
    return (
        <BooleanPill
            active={!user.data_limit_reached}
            activeLabel={t('left')}
            inactiveLabel={t('reached')}
        />
    )
}
