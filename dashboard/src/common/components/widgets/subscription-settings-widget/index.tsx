import * as React from 'react';
import { Icon, CommonIcons } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import { Link } from '@tanstack/react-router';
import { 
    SectionWidget, 
    Button,
    Separator
} from "@wildosvpn/common/components";
import { useSubscriptionSettingsQuery } from '@wildosvpn/modules/settings/subscription/services/subscription-settings.query';

export const SubscriptionSettingsWidget: React.FC = () => {
    const { t } = useTranslation();
    const { data: settings, isLoading } = useSubscriptionSettingsQuery();

    if (isLoading) {
        return (
            <SectionWidget
                title={<><Icon name="Settings" className="h-5 w-5" /> {t('Subscription Settings')}</>}
                description={t('Manage subscription configuration')}
                className="h-full"
            >
                <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
            </SectionWidget>
        );
    }

    return (
        <SectionWidget
            title={<><CommonIcons.Settings className="h-5 w-5" /> {t('Subscription Settings')}</>}
            description={t('Manage subscription configuration')}
            className="h-full"
        >
            <div className="space-y-4 w-full">
                {/* Key Settings Display */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Icon name="Globe" className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Profile Title</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                            {settings?.profile_title || 'Not set'}
                        </span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Icon name="Clock" className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Update Interval</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                            {settings?.update_interval || 0} minutes
                        </span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Icon name="Link2" className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Support Link</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                            {settings?.support_link ? 'Configured' : 'Not set'}
                        </span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Icon name="Settings" className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Template on Accept</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                            {settings?.template_on_acceptance ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Icon name="Settings" className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Rules Count</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                            {settings?.rules?.length || 0} rules
                        </span>
                    </div>
                </div>

                <Separator />

                {/* Action Button */}
                <div className="flex justify-center">
                    <Link to="/settings">
                        <Button variant="outline" className="w-full">
                            <Icon name="Settings" className="h-4 w-4 mr-2" />
                            Configure Settings
                        </Button>
                    </Link>
                </div>
            </div>
        </SectionWidget>
    );
};