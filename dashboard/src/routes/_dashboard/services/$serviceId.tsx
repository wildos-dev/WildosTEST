import {
    createFileRoute,
    defer,
    Await,
    Outlet,
} from "@tanstack/react-router";
import {
    RouterServiceContext,
    fetchService,
} from "@wildosvpn/modules/services";
import * as React from "react";
import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogTitle,
    Loading
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";

const ServiceProvider = () => {
    const { service } = Route.useLoaderData()
    return (
        <React.Suspense fallback={<Loading />}>
            <Await promise={service}>
                {(service) => (
                    <RouterServiceContext.Provider value={{ service }}>
                        <React.Suspense>
                            <Outlet />
                        </React.Suspense>
                    </RouterServiceContext.Provider>
                )}
            </Await>
        </React.Suspense>
    )
}

export const Route = createFileRoute('/_dashboard/services/$serviceId')({
    loader: async ({ params }) => {
        const servicePromise = fetchService({
            queryKey: ["services", Number.parseInt(params.serviceId)]
        });

        return {
            service: defer(servicePromise)
        }
    },
    errorComponent: () => {
        const { t } = useTranslation();
        return (
            <AlertDialog open={true}>
                <AlertDialogContent>
                    <AlertDialogTitle>{t('not-found.service')}</AlertDialogTitle>
                </AlertDialogContent>
            </AlertDialog>
        );
    },
    component: ServiceProvider,
})
