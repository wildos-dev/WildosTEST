import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router";
import { MutationDialog } from "@wildosvpn/modules/nodes";

const NodeCreate = () => {
    const search = useSearch({ from: "/_dashboard/nodes" });
    const navigate = useNavigate({ from: "/nodes/create" });
    return (
        <MutationDialog
            entity={null}
            onClose={() => navigate({ to: "/nodes", search })}
        />
    );
}

export const Route = createFileRoute("/_dashboard/nodes/create")({
    component: NodeCreate,
});
