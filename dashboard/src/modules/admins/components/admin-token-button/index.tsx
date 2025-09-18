import { useTranslation } from 'react-i18next';
import { useAdminTokenQuery } from '../../api/admin-token.query';
import { CopyToClipboardButton } from '@wildosvpn/common/components';
import { Icon } from '@wildosvpn/common/components/ui/icon';

export const AdminTokenButton = () => {
    const { t } = useTranslation();
    const { data } = useAdminTokenQuery();

    return (
        <CopyToClipboardButton
            text={data?.token || ''}
            successMessage={t('page.admins.token.copied')}
            copyIcon={(props: any) => <Icon name="Key" {...props} />}
            copyLabel={t('page.admins.token.copy')}
            errorLabel={t('page.admins.token.error')}
        />
    );
};