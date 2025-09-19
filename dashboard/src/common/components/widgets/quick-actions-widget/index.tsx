import * as React from 'react';
import { CommonIcons } from '@wildosvpn/common/components/ui/icon';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import { Link } from '@tanstack/react-router';
import { 
    SectionWidget, 
    Button
} from "@wildosvpn/common/components";

export const QuickActionsWidget: React.FC = () => {
    const { t } = useTranslation();

    const quickActions = [
        {
            label: t('widgets.quick-actions.create-user'),
            icon: CommonIcons.UserPlus,
            href: '/users/create',
            color: 'bg-blue-500 hover:bg-blue-600',
            textColor: 'text-white'
        },
        {
            label: t('widgets.quick-actions.add-node'),
            icon: CommonIcons.Server,
            href: '/nodes/create',
            color: 'bg-green-500 hover:bg-green-600',
            textColor: 'text-white'
        },
        {
            label: t('widgets.quick-actions.new-service'),
            icon: CommonIcons.Settings,
            href: '/services/create',
            color: 'bg-purple-500 hover:bg-purple-600',
            textColor: 'text-white'
        },
        {
            label: t('widgets.quick-actions.add-admin'),
            icon: CommonIcons.Shield,
            href: '/admins/create',
            color: 'bg-orange-500 hover:bg-orange-600',
            textColor: 'text-white'
        }
    ];

    return (
        <SectionWidget
            title={<><Icon name="Zap" className="h-5 w-5" /> {t('widgets.quick-actions.title')}</>}
            description={t('widgets.quick-actions.desc')}
            className="h-full"
        >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                {quickActions.map((action) => {
                    const Icon = action.icon;
                    return (
                        <Link key={action.href} to={action.href}>
                            <Button
                                className={`w-full h-16 sm:h-20 flex flex-col gap-2 ${action.color} ${action.textColor} transition-colors`}
                                variant="default"
                            >
                                <Icon className="h-5 w-5 sm:h-6 sm:w-6" />
                                <span className="text-xs sm:text-sm font-medium">{action.label}</span>
                            </Button>
                        </Link>
                    );
                })}
            </div>
        </SectionWidget>
    );
};