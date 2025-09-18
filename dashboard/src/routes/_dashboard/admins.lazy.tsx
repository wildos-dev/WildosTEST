import { Page, Loading } from '@wildosvpn/common/components'
import { SudoRoute } from '@wildosvpn/libs/sudo-routes'
import { createLazyFileRoute, Outlet } from '@tanstack/react-router'
import { AdminsTable } from '@wildosvpn/modules/admins'
import * as React from 'react'
import { useTranslation } from 'react-i18next'

export const AdminsPage: React.FC = () => {
  const { t } = useTranslation()
  return (
    <Page title={t('admins')}>
      <AdminsTable />
      <React.Suspense fallback={<Loading />}>
        <Outlet />
      </React.Suspense>
    </Page>
  )
}

export const Route = createLazyFileRoute('/_dashboard/admins')({
  component: () => (
    <SudoRoute>
      <AdminsPage />
    </SudoRoute>
  ),
})
