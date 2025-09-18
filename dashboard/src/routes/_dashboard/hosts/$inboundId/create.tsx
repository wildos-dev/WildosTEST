import * as React from "react";
import {
    createFileRoute,
    defer,
    Await,
    useNavigate,
} from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { HostsMutationDialog } from "@wildosvpn/modules/hosts";
import { fetchInbound } from "@wildosvpn/modules/inbounds";
import { Loading, AlertDialog, AlertDialogContent } from "@wildosvpn/common/components";

const HostCreate = () => {
    const { inboundId } = Route.useParams();
    const { inbound } = Route.useLoaderData()
    const navigate = useNavigate({ from: "/hosts/$inboundId/create" });

    return (
        <React.Suspense fallback={<Loading />}>
            <Await promise={inbound}>
                {(inbound) => (
                    <HostsMutationDialog
                        entity={null}
                        protocol={inbound.protocol}
                        inboundId={Number(inboundId)}
                        onClose={() => navigate({ to: "/hosts" })}
                    />
                )}
            </Await>
        </React.Suspense>
    );
}

export const Route = createFileRoute('/_dashboard/hosts/$inboundId/create')({
    loader: async ({ params }) => {
        const inboundPromise = fetchInbound({
            queryKey: ["inbounds", Number.parseInt(params.inboundId)]
        });

        return {
            inbound: defer(inboundPromise)
        }
    },
    errorComponent: () => {
        const { t } = useTranslation();
        return (
            <AlertDialog open={true}>
                <AlertDialogContent>{t('not_found.host')}</AlertDialogContent>
            </AlertDialog>
        );
    },
    component: HostCreate,
});
