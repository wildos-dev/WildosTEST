import { createLazyFileRoute } from '@tanstack/react-router'
import { Page } from '@wildosvpn/common/components'
import { UsersStatsWidget, useUsersStatsQuery } from '@wildosvpn/modules/users'
import { TotalTrafficsWidgetLazy } from '@wildosvpn/features/total-traffic-widget/lazy'
import { 
  NodesStatsWidget, 
  useNodesStatsQuery, 
  AllBackendsStatsWidget, 
  useGlobalBackendsStatsQuery,
  HostSystemMetricsWidget,
  PeakEventsWidget,
  TopUsageNodesWidget,
  NetworkActivityWidget
} from '@wildosvpn/modules/nodes'
import { AdminsStatsWidget, useAdminsStatsQuery } from '@wildosvpn/modules/admins'
import { 
  SystemOverviewWidget,
  QuickActionsWidget,
  SubscriptionSettingsWidget,
  RecentSubscriptionUpdatesWidget
} from '@wildosvpn/common/components/widgets'
import { WidgetErrorBoundary } from '@wildosvpn/common/components'
import { useDashboardSettings } from '@wildosvpn/common/hooks'
import { useTranslation } from 'react-i18next'
import * as React from 'react'

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation()
  const { isWidgetVisible } = useDashboardSettings()
  
  // Fetch data for all widgets
  const { data: usersData } = useUsersStatsQuery()
  const { data: nodesData } = useNodesStatsQuery()
  const { data: adminsData } = useAdminsStatsQuery()
  const { data: allBackendsData } = useGlobalBackendsStatsQuery()

  // Calculate which widgets to show
  const showTrafficWidget = isWidgetVisible('totalTraffics')
  const showUsersStatsWidget = isWidgetVisible('usersStats') && usersData.total !== 0
  const showNodesStatsWidget = isWidgetVisible('nodesStats') && nodesData.total !== 0
  const showAdminsStatsWidget = isWidgetVisible('adminsStats') && adminsData.total !== 0
  const showAllBackendsStatsWidget = isWidgetVisible('allBackendsStats') && allBackendsData && allBackendsData.totalBackends > 0
  const showSystemOverviewWidget = isWidgetVisible('systemOverview')
  const showHostSystemMetricsWidget = isWidgetVisible('hostSystemMetrics')
  const showPeakEventsWidget = isWidgetVisible('peakEvents')
  const showTopUsageNodesWidget = isWidgetVisible('topUsageNodes')
  const showNetworkActivityWidget = isWidgetVisible('networkActivity')
  const showQuickActionsWidget = isWidgetVisible('quickActions')
  const showSubscriptionSettingsWidget = isWidgetVisible('subscriptionSettings')
  const showRecentSubscriptionUpdatesWidget = isWidgetVisible('recentSubscriptionUpdates')

  // Calculate visible widgets count for layout
  const visibleWidgets = [
    showTrafficWidget,
    showUsersStatsWidget,
    showNodesStatsWidget,
    showAdminsStatsWidget,
    showAllBackendsStatsWidget,
    showSystemOverviewWidget,
    showHostSystemMetricsWidget,
    showPeakEventsWidget,
    showTopUsageNodesWidget,
    showNetworkActivityWidget,
    showQuickActionsWidget,
    showSubscriptionSettingsWidget,
    showRecentSubscriptionUpdatesWidget
  ].filter(Boolean).length

  const hasAnyWidget = visibleWidgets > 0

  return (
    <Page className="flex flex-col gap-4 w-full" title={t('home')}>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
        {/* Main traffic widget - takes most space if present */}
        {showTrafficWidget && (
          <div className={showUsersStatsWidget || showSystemOverviewWidget ? "md:col-span-8" : "md:col-span-12"}>
            <WidgetErrorBoundary widgetName={t('widget-names.traffic-analytics')}>
              <TotalTrafficsWidgetLazy />
            </WidgetErrorBoundary>
          </div>
        )}

        {/* Users stats widget */}
        {showUsersStatsWidget && (
          <div className={showTrafficWidget ? "md:col-span-4" : "md:col-span-6"}>
            <UsersStatsWidget {...usersData} />
          </div>
        )}

        {/* System overview widget - wide widget */}
        {showSystemOverviewWidget && (
          <div className={showTrafficWidget ? "md:col-span-4" : "md:col-span-12"}>
            <SystemOverviewWidget />
          </div>
        )}

        {/* Nodes stats widget */}
        {showNodesStatsWidget && (
          <div className="md:col-span-4">
            <NodesStatsWidget {...nodesData} />
          </div>
        )}

        {/* All backends stats widget */}
        {showAllBackendsStatsWidget && allBackendsData && (
          <div className="md:col-span-4">
            <AllBackendsStatsWidget {...allBackendsData} />
          </div>
        )}

        {/* Admins stats widget */}
        {showAdminsStatsWidget && (
          <div className="md:col-span-4">
            <AdminsStatsWidget {...adminsData} />
          </div>
        )}

        {/* Host System Metrics widget */}
        {showHostSystemMetricsWidget && (
          <div className="md:col-span-6">
            <WidgetErrorBoundary widgetName={t('widget-names.host-system-metrics')}>
              <HostSystemMetricsWidget />
            </WidgetErrorBoundary>
          </div>
        )}

        {/* Peak Events widget */}
        {showPeakEventsWidget && (
          <div className="md:col-span-6">
            <WidgetErrorBoundary widgetName={t('widget-names.peak-events')}>
              <PeakEventsWidget />
            </WidgetErrorBoundary>
          </div>
        )}

        {/* Top Usage Nodes widget */}
        {showTopUsageNodesWidget && (
          <div className="md:col-span-6">
            <WidgetErrorBoundary widgetName={t('widget-names.top-usage-nodes')}>
              <TopUsageNodesWidget />
            </WidgetErrorBoundary>
          </div>
        )}

        {/* Network Activity widget */}
        {showNetworkActivityWidget && (
          <div className="md:col-span-6">
            <WidgetErrorBoundary widgetName={t('widget-names.network-activity')}>
              <NetworkActivityWidget />
            </WidgetErrorBoundary>
          </div>
        )}

        {/* Quick Actions widget */}
        {showQuickActionsWidget && (
          <div className="md:col-span-4">
            <WidgetErrorBoundary widgetName={t('widget-names.quick-actions')}>
              <QuickActionsWidget />
            </WidgetErrorBoundary>
          </div>
        )}

        {/* Subscription Settings widget */}
        {showSubscriptionSettingsWidget && (
          <div className="md:col-span-4">
            <SubscriptionSettingsWidget />
          </div>
        )}

        {/* Recent Subscription Updates widget */}
        {showRecentSubscriptionUpdatesWidget && (
          <div className="md:col-span-4">
            <RecentSubscriptionUpdatesWidget />
          </div>
        )}


        {/* No widgets message */}
        {!hasAnyWidget && (
          <div className="md:col-span-12 flex items-center justify-center p-8">
            <div className="text-center text-muted-foreground">
              <h3 className="text-lg font-semibold mb-2">{t('dashboard.no-widgets-configured')}</h3>
              <p>{t('dashboard.configure-widgets-description')}</p>
            </div>
          </div>
        )}
      </div>
    </Page>
  )
}

export const Route = createLazyFileRoute('/_dashboard/')({
  component: () => <DashboardPage />,
})
