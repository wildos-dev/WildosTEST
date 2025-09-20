import { Page } from '@wildosvpn/common/components'
import { SubscriptionSettingsWidget } from '@wildosvpn/modules/settings/subscription'
import { createLazyFileRoute } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'
import { SudoRoute } from '@wildosvpn/libs/sudo-routes'

export const Settings = () => {
  const { t } = useTranslation()
  return (
    <Page
      title={t('settings')}
      className="p-4 sm:p-6"
    >
      <div className="space-y-4 sm:space-y-6 max-w-4xl">
        {/* Settings sections with responsive layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <div className="space-y-4 sm:space-y-6">
            <SubscriptionSettingsWidget />
          </div>
          <div className="space-y-4 sm:space-y-6">
            {/* Configuration Widget placeholder */}
          </div>
        </div>
      </div>
    </Page>
  )
}

export const Route = createLazyFileRoute('/_dashboard/settings')({
  component: () => (
    <SudoRoute>
      {' '}
      <Settings />{' '}
    </SudoRoute>
  ),
})
