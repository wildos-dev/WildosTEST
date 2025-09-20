import * as React from 'react';
import { Icon, CommonIcons } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import { 
    SectionWidget,
    ScrollArea,
    Separator
} from "@wildosvpn/common/components";
import { useUsersStatsQuery } from '@wildosvpn/modules/users';

export const RecentSubscriptionUpdatesWidget: React.FC = () => {
    const { t } = useTranslation();
    const { data: usersStats, isLoading } = useUsersStatsQuery();

    // Since API returns descriptions only, we show static 'Recently' indicator

    const recentUpdates = usersStats?.recent_subscription_updates || [];

    if (isLoading) {
        return (
            <SectionWidget
                title={<><Icon name="Bell" className="h-5 w-5" /> {t('widgets.recent_updates')}</>}
                description={t('widgets.latest_subscription_changes')}
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
            title={<><CommonIcons.Bell className="h-5 w-5" /> {t('widgets.recent_updates')}</>}
            description={t('widgets.latest_subscription_changes')}
            className="h-full"
        >
            <div className="w-full">
                {recentUpdates.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                        <Icon name="Bell" className="h-12 w-12 text-muted-foreground mb-4" />
                        <p className="text-sm text-muted-foreground">{t('widgets.no_recent_updates')}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                            {t('widgets.subscription_updates_will_appear')}
                        </p>
                    </div>
                ) : (
                    <ScrollArea className="h-[250px]">
                        <div className="space-y-3">
                            {recentUpdates.map((update, index) => (
                                <div key={index}>
                                    <div className="flex items-start gap-3 p-2 rounded-lg bg-muted/50">
                                        <Icon name="User" className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">
                                                {update || t('widgets.subscription_updated')}
                                            </p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {t('widgets.recently')}
                                            </p>
                                        </div>
                                    </div>
                                    {index < recentUpdates.length - 1 && (
                                        <Separator className="my-2" />
                                    )}
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                )}
            </div>
        </SectionWidget>
    );
};