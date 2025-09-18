import {
    createFileRoute,
    useNavigate,
    useSearch,
} from "@tanstack/react-router";
import {
    MutationDialog,
    useRouterNodeContext,
} from "@wildosvpn/modules/nodes";

const NodeEdit = () => {
    const value = useRouterNodeContext()
    const search = useSearch({ from: "/_dashboard/nodes" });
    const navigate = useNavigate({ from: "/nodes/$nodeId/edit" });

    return value && (
        <MutationDialog
            entity={value.node}
            onClose={() => navigate({ to: "/nodes", search })}
        />
    );
}

export const Route = createFileRoute('/_dashboard/nodes/$nodeId/edit')({
    component: NodeEdit
})
