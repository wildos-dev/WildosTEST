import {
    createFileRoute,
    defer,
    Await,
    Outlet
} from "@tanstack/react-router";
import {
    fetchNode,
    RouterNodeContext
} from "@wildosvpn/modules/nodes";
import * as React from "react";
import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogTitle,
    Loading,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";

const NodeProvider = () => {
    const { node } = Route.useLoaderData()

    return (
        <React.Suspense fallback={<Loading />}>
            <Await promise={node}>
                {(node) => (
                    <RouterNodeContext.Provider value={{ node }}>
                        <React.Suspense>
                            <Outlet />
                        </React.Suspense>
                    </RouterNodeContext.Provider>
                )}
            </Await>
        </React.Suspense>
    );
};

export const Route = createFileRoute('/_dashboard/nodes/$nodeId')({
    loader: async ({ params }) => {
        const nodePromise = fetchNode({
            queryKey: ["nodes", Number.parseInt(params.nodeId)]
        });

        return {
            node: defer(nodePromise)
        }
    },
    component: NodeProvider,
    errorComponent: () => {
        const { t } = useTranslation();
        return (
            <AlertDialog open={true}>
                <AlertDialogContent>
                    <AlertDialogTitle>{t('not-found.node')}</AlertDialogTitle>
                </AlertDialogContent>
            </AlertDialog>
        );
    },
})
