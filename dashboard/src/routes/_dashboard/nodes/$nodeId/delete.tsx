import {
    createFileRoute,
    useNavigate,
    useSearch,
} from "@tanstack/react-router";
import {
    NodesDeleteConfirmationDialog,
    useRouterNodeContext,
} from "@wildosvpn/modules/nodes";
import { useDialog } from "@wildosvpn/common/hooks";

const NodeDelete = () => {
    const [deleteDialogOpen, setDeleteDialogOpen] = useDialog(true);
    const value = useRouterNodeContext()
    const search = useSearch({ from: "/_dashboard/nodes" });
    const navigate = useNavigate({ from: "/nodes/$nodeId/delete" });

    return value && (
        <NodesDeleteConfirmationDialog
            open={deleteDialogOpen}
            onOpenChange={setDeleteDialogOpen}
            entity={value.node}
            onClose={() => navigate({ to: "/nodes", search })}
        />
    );
}

export const Route = createFileRoute('/_dashboard/nodes/$nodeId/delete')({
    component: NodeDelete,
})
