import { SidebarObject } from '@wildosvpn/common/components';
import { Icon } from '@wildosvpn/common/components';
import { useTranslation } from 'react-i18next';

export const useSidebarItems = () => {
    const { t } = useTranslation();
    
    const sidebarItems: SidebarObject = {
        [t('dashboard')]: [
            {
                title: t('home'),
                to: '/',
                icon: <Icon name="Home" />,
                isParent: false,
            },
        ],
        [t('management')]: [
            {
                title: t('users'),
                to: '/users',
                icon: <Icon name="Users" />,
                isParent: false,
            },
            {
                title: t('services'),
                to: '/services',
                icon: <Icon name="Server" />,
                isParent: false,
            },
            {
                title: t('nodes'),
                to: '/nodes',
                icon: <Icon name="Box" />,
                isParent: false,
            },
            {
                title: t('hosts'),
                to: '/hosts',
                icon: <Icon name="ServerCog" />,
                isParent: false,
            },
        ],
        [t('system')]: [
            {
                title: t('admins'),
                to: '/admins',
                icon: <Icon name="ShieldCheck" />,
                isParent: false,
            },
            {
                title: t('settings'),
                to: '/settings',
                icon: <Icon name="Settings" />,
                isParent: false,
            },
        ]
    };

    const sidebarItemsNonSudoAdmin: SidebarObject = {
        [t('dashboard')]: [
            {
                title: t('home'),
                to: '/',
                icon: <Icon name="Home" />,
                isParent: false,
            },
        ],
        [t('management')]: [
            {
                title: t('users'),
                to: '/users',
                icon: <Icon name="Users" />,
                isParent: false,
            },
        ],
    };

    return { sidebarItems, sidebarItemsNonSudoAdmin };
};

