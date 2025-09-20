import * as React from 'react';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import { SectionWidget } from "@wildosvpn/common/components";
import { useUsersStatsQuery } from "@wildosvpn/modules/users";
import { useNodesStatsQuery } from "@wildosvpn/modules/nodes";
import { useAdminsStatsQuery } from "@wildosvpn/modules/admins";

interface MetricCardProps {
    icon: React.ReactNode;
    label: string;
    value: number;
    subValue?: number;
    subLabel?: string;
    status?: 'success' | 'warning' | 'error' | 'neutral';
}

const MetricCard: React.FC<MetricCardProps> = ({ icon, label, value, subValue, subLabel, status = 'neutral' }) => {
    const statusColors = {
        success: 'text-green-600',
        warning: 'text-yellow-600',
        error: 'text-red-600',
        neutral: 'text-foreground'
    };

    return (
        <div className="p-3 sm:p-4 rounded-lg border bg-card/50 min-w-0">
            <div className="flex items-center gap-2 sm:gap-3">
                <div className="text-muted-foreground flex-shrink-0">{icon}</div>
                <div className="flex-1 min-w-0">
                    <div className={`text-xl sm:text-2xl font-bold truncate ${statusColors[status]}`}>
                        {value || 0}
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground truncate">{label}</div>
                    {subValue !== undefined && (
                        <div className="text-xs text-muted-foreground mt-1 truncate">
                            {subValue} {subLabel}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export const SystemOverviewWidget: React.FC = () => {
    const { t } = useTranslation();
    const { data: usersStats } = useUsersStatsQuery();
    const { data: nodesStats } = useNodesStatsQuery();
    const { data: adminsStats } = useAdminsStatsQuery();

    // Calculate status for nodes with safe access
    const nodesTotal = nodesStats?.total || 0;
    const nodesUnhealthy = nodesStats?.unhealthy || 0;
    const nodesStatus = nodesTotal === 0 ? 'neutral' : 
                       nodesUnhealthy > 0 ? 'error' : 'success';

    // Calculate status for users with safe access
    const usersTotal = usersStats?.total || 0;
    const usersActive = usersStats?.active || 0;
    const usersActivePercentage = usersTotal > 0 ? 
                                  Math.round((usersActive / usersTotal) * 100) : 0;
    const usersStatus = usersTotal === 0 ? 'neutral' :
                        usersActivePercentage < 50 ? 'warning' : 'success';

    return (
        <SectionWidget
            title={
                <>
                    <Icon name="Activity" /> {t('system-overview', 'System Overview')}
                </>
            }
            description={t('page.home.system-overview.desc', 'Key system metrics at a glance')}
            className="h-full"
        >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 w-full">
                {/* Users Stats */}
                <MetricCard
                    icon={<Icon name="Users" className="h-5 w-5" />}
                    label={t('total-users', 'Total Users')}
                    value={usersTotal}
                    subValue={usersStats?.online || 0}
                    subLabel={t('online', 'online')}
                    status={usersStatus}
                />

                {/* Active Users */}
                <MetricCard
                    icon={<Icon name="Eye" className="h-5 w-5" />}
                    label={t('active-users', 'Active Users')}
                    value={usersActive}
                    subValue={usersStats?.expired || 0}
                    subLabel={t('expired', 'expired')}
                    status={usersActive > 0 ? 'success' : 'neutral'}
                />

                {/* Nodes Stats */}
                <MetricCard
                    icon={<Icon name="Server" className="h-5 w-5" />}
                    label={t('total-nodes', 'Total Nodes')}
                    value={nodesTotal}
                    subValue={nodesStats?.healthy || 0}
                    subLabel={t('healthy', 'healthy')}
                    status={nodesStatus}
                />

                {/* Unhealthy Nodes */}
                {nodesUnhealthy > 0 && (
                    <MetricCard
                        icon={<Icon name="AlertTriangle" className="h-5 w-5" />}
                        label={t('unhealthy-nodes', 'Issues')}
                        value={nodesUnhealthy}
                        subLabel={t('nodes-need-attention', 'nodes need attention')}
                        status="error"
                    />
                )}

                {/* Admins */}
                <MetricCard
                    icon={<Icon name="Shield" className="h-5 w-5" />}
                    label={t('total-admins', 'Total Admins')}
                    value={adminsStats?.total || 0}
                    status="neutral"
                />

                {/* Data Limit Issues */}
                {(usersStats?.limited || 0) > 0 && (
                    <MetricCard
                        icon={<Icon name="AlertTriangle" className="h-5 w-5" />}
                        label={t('limited-users', 'Data Limit Reached')}
                        value={usersStats?.limited || 0}
                        subLabel={t('users', 'users')}
                        status="warning"
                    />
                )}
            </div>
        </SectionWidget>
    );
};