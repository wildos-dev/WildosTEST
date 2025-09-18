import { useTranslation } from 'react-i18next';
import { useCertificateQuery } from '../api';
import { CopyToClipboardButton } from '@wildosvpn/common/components';
import { Icon } from '@wildosvpn/common/components/ui/icon';

export const CertificateButton = ({ className }: { className?: string }) => {
    const { t } = useTranslation();
    const { data: certificate } = useCertificateQuery();

    return (
        <CopyToClipboardButton
            text={certificate}
            successMessage={t('page.settings.certificate.copied')}
            copyIcon={(props: any) => <Icon name="ClipboardCopy" {...props} />}
            copyLabel={t('page.settings.certificate.copy')}
            errorLabel={t('page.settings.certificate.error')}
            className={className}
        />
    );
};
