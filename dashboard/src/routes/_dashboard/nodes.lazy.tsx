import { Page, Loading } from '@wildosvpn/common/components'
import { NodesGrid } from '@wildosvpn/modules/nodes'
import { createLazyFileRoute, Outlet } from '@tanstack/react-router'
import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { SudoRoute } from '@wildosvpn/libs/sudo-routes'
import { z } from 'zod'
import { nodesSearchSchema } from './nodes'

export type NodesSearch = z.infer<typeof nodesSearchSchema>

export const NodesPage: React.FC = () => {
  const { t } = useTranslation()
  return (
    <Page
      title={t('nodes')}
      className="sm:w-screen md:w-full"
    >
      <NodesGrid />
      <React.Suspense fallback={<Loading />}>
        <Outlet />
      </React.Suspense>
    </Page>
  )
}

export const Route = createLazyFileRoute('/_dashboard/nodes')({
  component: () => (
    <SudoRoute>
      <NodesPage />
    </SudoRoute>
  ),
})
