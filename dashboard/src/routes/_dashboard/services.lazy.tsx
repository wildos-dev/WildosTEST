import { Page, Loading } from '@wildosvpn/common/components'
import { ServicesTable } from '@wildosvpn/modules/services'
import { createLazyFileRoute, Outlet } from '@tanstack/react-router'
import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { SudoRoute } from '@wildosvpn/libs/sudo-routes'

export const ServicesPage: React.FC = () => {
  const { t } = useTranslation()
  return (
    <Page title={t('services')}>
      <ServicesTable />
      <React.Suspense fallback={<Loading />}>
        <Outlet />
      </React.Suspense>
    </Page>
  )
}

export const Route = createLazyFileRoute('/_dashboard/services')({
  component: () => (
    <SudoRoute>
      {' '}
      <ServicesPage />{' '}
    </SudoRoute>
  ),
})
