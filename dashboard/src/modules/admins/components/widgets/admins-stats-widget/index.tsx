import * as React from 'react';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import { SectionWidget } from "@wildosvpn/common/components";

interface AdminsStatsProps {
    total: number;
}

export const AdminsStatsWidget: React.FC<AdminsStatsProps> = ({ total }) => {
    const { t } = useTranslation();

    return (
        <SectionWidget
            title={<> <Icon name="Shield" /> {t('admins')} </>}
            description={t('page.home.admins-stats.desc', 'Total number of admin users')}
            className="h-full"
        >
            <div className="flex flex-col items-center justify-center py-4 sm:py-8">
                <div className="flex items-center gap-3 sm:gap-4">
                    <Icon name="Users" className="h-8 w-8 sm:h-12 sm:w-12 text-muted-foreground" />
                    <div className="text-center">
                        <div className="text-2xl sm:text-4xl font-bold text-foreground">
                            {total || 0}
                        </div>
                        <div className="text-xs sm:text-sm text-muted-foreground mt-1">
                            {t('total-admins', 'Total Admins')}
                        </div>
                    </div>
                </div>
            </div>
        </SectionWidget>
    );
};