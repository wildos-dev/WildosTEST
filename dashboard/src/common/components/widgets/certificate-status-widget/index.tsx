import * as React from 'react';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import { Link } from '@tanstack/react-router';
import { 
    SectionWidget, 
    Button,
    Badge,
    Separator
} from "@wildosvpn/common/components";

// Simple certificate status interface
interface CertificateStatus {
    ca_certificate: {
        status: 'valid' | 'warning' | 'invalid';
        expires_in_days: number;
    };
    server_certificate: {
        status: 'valid' | 'warning' | 'invalid';
        expires_in_days: number;
    };
    overall_status: 'healthy' | 'warning' | 'critical';
}

export const CertificateStatusWidget: React.FC = () => {
    const { t } = useTranslation();

    // Mock certificate status - in real implementation, this would come from an API
    const certificateStatus: CertificateStatus = {
        ca_certificate: {
            status: 'valid',
            expires_in_days: 2847
        },
        server_certificate: {
            status: 'valid',
            expires_in_days: 89
        },
        overall_status: 'healthy'
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'valid':
                return <Icon name="CheckCircle" className="h-4 w-4 text-green-500" />;
            case 'warning':
                return <Icon name="AlertTriangle" className="h-4 w-4 text-yellow-500" />;
            case 'invalid':
                return <Icon name="AlertTriangle" className="h-4 w-4 text-red-500" />;
            default:
                return <Icon name="AlertTriangle" className="h-4 w-4 text-gray-500" />;
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'healthy':
                return <Badge variant="default" className="bg-green-100 text-green-800">{t('widgets.certificate-status.status.healthy')}</Badge>;
            case 'warning':
                return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">{t('widgets.certificate-status.status.warning')}</Badge>;
            case 'critical':
                return <Badge variant="destructive">{t('widgets.certificate-status.status.critical')}</Badge>;
            default:
                return <Badge variant="outline">{t('widgets.certificate-status.status.unknown')}</Badge>;
        }
    };

    const formatDaysLeft = (days: number) => {
        if (days > 365) {
            return `${Math.floor(days / 365)}${t('widgets.certificate-status.time-units.years-short')} ${days % 365}${t('widgets.certificate-status.time-units.days-short')}`;
        }
        return `${days} ${t('widgets.certificate-status.time-units.days')}`;
    };

    return (
        <SectionWidget
            title={<><Icon name="Shield" className="h-5 w-5" /> {t('widgets.certificate-status.title')}</>}
            description={t('widgets.certificate-status.desc')}
            className="h-full"
        >
            <div className="space-y-4 w-full">
                {/* Overall Status */}
                <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{t('widgets.certificate-status.overall-status')}</span>
                    {getStatusBadge(certificateStatus.overall_status)}
                </div>

                <Separator />

                {/* Certificate Details */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {getStatusIcon(certificateStatus.ca_certificate.status)}
                            <span className="text-sm font-medium">{t('widgets.certificate-status.ca-certificate')}</span>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-muted-foreground">
                                {formatDaysLeft(certificateStatus.ca_certificate.expires_in_days)} {t('widgets.certificate-status.time-left')}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {getStatusIcon(certificateStatus.server_certificate.status)}
                            <span className="text-sm font-medium">{t('widgets.certificate-status.server-certificate')}</span>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-muted-foreground">
                                {formatDaysLeft(certificateStatus.server_certificate.expires_in_days)} {t('widgets.certificate-status.time-left')}
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Management Button */}
                <div className="flex justify-center">
                    <Link to="/settings">
                        <Button variant="outline" className="w-full">
                            <Icon name="Settings" className="h-4 w-4 mr-2" />
                            {t('widgets.certificate-status.manage-certificates')}
                        </Button>
                    </Link>
                </div>
            </div>
        </SectionWidget>
    );
};