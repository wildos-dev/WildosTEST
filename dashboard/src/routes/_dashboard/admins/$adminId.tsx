import {
    createFileRoute,
    Outlet,
} from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { queryClient } from "@wildosvpn/common/utils";
import {
    RouterAdminContext,
    adminQueryOptions,
} from "@wildosvpn/modules/admins";
import * as React from "react";
import {
    AlertDialog,
    AlertDialogContent,
    Loading,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";

const AdminProvider = () => {
    const { username } = Route.useLoaderData()
    const { data: admin, isPending } = useSuspenseQuery(adminQueryOptions({ username }))
    const value = React.useMemo(() => ({ admin, isPending }), [admin, isPending])
    return (
        <RouterAdminContext.Provider value={value}>
            <React.Suspense fallback={<Loading />}>
                <Outlet />
            </React.Suspense>
        </RouterAdminContext.Provider>
    )
}

export const Route = createFileRoute('/_dashboard/admins/$adminId')({
    loader: async ({ params }) => {
        queryClient.ensureQueryData(adminQueryOptions({ username: params.adminId }))
        return { username: params.adminId };
    },
    errorComponent: () => {
        const { t } = useTranslation();
        return (
            <AlertDialog open={true}>
                <AlertDialogContent>{t('not-found.admin')}</AlertDialogContent>
            </AlertDialog>
        );
    },
    component: AdminProvider,
})
