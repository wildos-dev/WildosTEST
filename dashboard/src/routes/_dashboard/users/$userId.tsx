import {
    createFileRoute,
    Outlet,
} from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { queryClient } from "@wildosvpn/common/utils";
import {
    RouterUserContext,
    userQueryOptions,
} from "@wildosvpn/modules/users";
import * as React from "react";
import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogTitle,
    Loading,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { z } from 'zod';

const UserProvider = () => {
    const data = Route.useLoaderData();
    const username = data?.username ?? "";
    const { t } = useTranslation();
    
    if (!username) {
        return (
            <AlertDialog open={true}>
                <AlertDialogContent>
                    <AlertDialogTitle>{t('not-found.user')}</AlertDialogTitle>
                </AlertDialogContent>
            </AlertDialog>
        );
    }
    
    const { data: user, isPending } = useSuspenseQuery(userQueryOptions({ username }))
    const value = React.useMemo(() => ({ user, isPending }), [user, isPending])
    return (
        <RouterUserContext.Provider value={value}>
            <React.Suspense fallback={<Loading />}>
                <Outlet />
            </React.Suspense>
        </RouterUserContext.Provider>
    )
}

const ParamsSchema = z.object({ userId: z.string().min(1) });

export const Route = createFileRoute('/_dashboard/users/$userId')({
    loader: async ({ params }) => {
        const { userId } = ParamsSchema.parse(params);
        queryClient.ensureQueryData(userQueryOptions({ username: userId }))
        return { username: userId };
    },
    errorComponent: () => {
        const { t } = useTranslation();
        return (
            <AlertDialog open={true}>
                <AlertDialogContent>
                    <AlertDialogTitle>{t('not-found.user')}</AlertDialogTitle>
                </AlertDialogContent>
            </AlertDialog>
        );
    },
    component: UserProvider,
})
