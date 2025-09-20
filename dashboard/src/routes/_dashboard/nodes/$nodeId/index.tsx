import {
    createFileRoute,
    useNavigate,
    useSearch,
} from "@tanstack/react-router";
import {
    useRouterNodeContext,
    NodesSettingsDialog,
} from "@wildosvpn/modules/nodes";
import { useDialog } from "@wildosvpn/common/hooks";

const NodeOpen = () => {
    const [settingsDialogOpen, setSettingsDialogOpen] = useDialog(true);
    const value = useRouterNodeContext()
    const search = useSearch({ from: "/_dashboard/nodes" });
    const navigate = useNavigate({ from: "/nodes/$nodeId" });

    return value && (
        <NodesSettingsDialog
            open={settingsDialogOpen}
            onOpenChange={setSettingsDialogOpen}
            node={value.node}
            onClose={() => navigate({ to: "/nodes", search })}
        />
    );
}

export const Route = createFileRoute('/_dashboard/nodes/$nodeId/')({
    component: NodeOpen
})
