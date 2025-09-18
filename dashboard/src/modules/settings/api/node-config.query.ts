import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

export const NodeConfigQueryFetchKey = "node-config";

type NodeConfigResponse = {
    port: number;
};

const fetchNodeConfig = (): Promise<NodeConfigResponse> =>
    fetch("/system/config/node-grpc-port");

export const useNodeConfigQuery = () => {
    return useQuery({
        queryKey: [NodeConfigQueryFetchKey],
        queryFn: fetchNodeConfig,
        initialData: { port: 62050 }
    });
};