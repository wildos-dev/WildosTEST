import type { NodeType } from "@wildosvpn/modules/nodes";
import { useMutation } from "@tanstack/react-query";
import { fetch, queryClient } from "@wildosvpn/common/utils";
import { toast } from "sonner";
import i18n from "@wildosvpn/features/i18n";

interface RestartBackendRequest {
    node: NodeType;
    backend: string;
}

export async function fetchRestartBackend({
    node,
    backend,
}: RestartBackendRequest): Promise<void> {
    return fetch(`/nodes/${node.id}/${backend}/restart`, {
        method: "post",
    });
}

const handleError = (error: Error, value: RestartBackendRequest) => {
    toast.error(
        i18n.t("page.nodes.restart.error", { 
            name: value.node.name, 
            backend: value.backend 
        }),
        {
            description: error.message,
        }
    );
};

const handleSuccess = (_: void, value: RestartBackendRequest) => {
    toast.success(
        i18n.t("page.nodes.restart.success.title", { 
            backend: value.backend 
        }),
        {
            description: i18n.t("page.nodes.restart.success.desc"),
        }
    );
    // Invalidate backend stats to refetch status
    queryClient.invalidateQueries({ 
        queryKey: ["nodes", value.node.id, value.backend, "stats"] 
    });
};

const RestartBackendFetchKey = ["nodes", "restart"];

export const useRestartBackendMutation = () => {
    return useMutation({
        mutationKey: RestartBackendFetchKey,
        mutationFn: fetchRestartBackend,
        onError: handleError,
        onSuccess: handleSuccess,
    });
};