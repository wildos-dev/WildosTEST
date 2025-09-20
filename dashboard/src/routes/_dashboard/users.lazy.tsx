import { Page, Loading } from '@wildosvpn/common/components'
import { UsersNoServiceAlert, UsersTable } from '@wildosvpn/modules/users'
import { createLazyFileRoute, Outlet } from '@tanstack/react-router'
import * as React from 'react'
import { useTranslation } from 'react-i18next'

export const UsersPage: React.FC = () => {
  const { t } = useTranslation()

  return (
    <Page title={t('users')} footer={<UsersNoServiceAlert />}>
      <UsersTable />
      <React.Suspense fallback={<Loading />}>
        <Outlet />
      </React.Suspense>
    </Page>
  )
}

export const Route = createLazyFileRoute('/_dashboard/users')({
  component: () => <UsersPage />,
})
