import * as React from 'react';
import { UserProp } from "@wildosvpn/modules/users";
import { useTranslation } from "react-i18next";
import { format, formatDistanceToNow } from "date-fns";

export const UserExpirationValue: React.FC<UserProp> = ({ user }) => {
    const { t } = useTranslation();

    return ({
        start_on_first_use: user.usage_duration && `${(user.usage_duration / 86400)} Day`,
        fixed_date: user.expire_date && (format(new Date(user.expire_date), "MMMM do, yyyy") + ' (' + formatDistanceToNow(new Date(user.expire_date), { addSuffix: true }) + ')'),
        never: t('never'),
    }[user.expire_strategy])
}

