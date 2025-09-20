
import { Button } from '@wildosvpn/common/components';
import { Icon } from '@wildosvpn/common/components';
import * as React from 'react';
import { useTranslation } from 'react-i18next';

interface ToggleButtonProps {
    collapsed: boolean;
    onToggle: () => void;
}

export const ToggleButton: React.FC<ToggleButtonProps> = ({ collapsed, onToggle }) => {
    const { t } = useTranslation();
    const IconName = collapsed ? "PanelLeftClose" : "PanelLeftOpen";

    return (
        <Button 
            className="p-2 bg-secondary-foreground border-2 text-primary-foreground dark:bg-secondary dark:text-primary" 
            onClick={onToggle}
            aria-label={collapsed ? t("features.sidebar.expand-sidebar") : t("features.sidebar.collapse-sidebar")}
        >
            <Icon name={IconName} className="w-full h-full" />
        </Button>
    );
};
