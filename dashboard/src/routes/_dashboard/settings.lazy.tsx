import { Page, VStack } from '@wildosvpn/common/components'
import { CertificateWidget } from '@wildosvpn/modules/settings'
import { SubscriptionSettingsWidget } from '@wildosvpn/modules/settings/subscription'
import { createLazyFileRoute } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'
import { SudoRoute } from '@wildosvpn/libs/sudo-routes'

export const Settings = () => {
  const { t } = useTranslation()
  return (
    <Page
      title={t('settings')}
      className="sm:flex flex-col lg:grid grid-cols-2 gap-3 h-full"
    >
      {/* <ConfigurationWidget /> */}
      <VStack className="gap-3">
        <SubscriptionSettingsWidget />
        <CertificateWidget />
      </VStack>
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
