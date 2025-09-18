import type { StatusType } from "@wildosvpn/common/types/status";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { z } from "zod";

export const NodesStatus = {
    healthy: {
        label: "healthy",
        icon: (props: any) => <Icon name="Zap" {...props} />,
    },
    unhealthy: {
        label: "unhealthy",
        icon: (props: any) => <Icon name="ZapOff" {...props} />,
    },
    disabled: {
        label: "disabled",
        icon: (props: any) => <Icon name="PowerOff" {...props} />,
    },
    none: {
        label: "none",
        icon: null,
    },
} as Record<string, StatusType>;

export const NodeSchema = z.object({
    name: z.string().min(1),
    address: z.string().min(1),
    port: z
        .number()
        .min(1)
        .or(z.string().transform((v) => Number.parseFloat(v))),
    id: z.number().nullable().optional(),
    status: z.enum([
        NodesStatus.healthy.label,
        NodesStatus.unhealthy.label,
        "none",
        NodesStatus.disabled.label,
    ]),
    usage_coefficient: z
        .number()
        .default(1.0)
        .or(z.string().transform((v) => Number.parseFloat(v))),
    connection_backend: z.enum(["grpclib"]).default("grpclib"),
});

export type NodeBackendType = {
    name: string;
    backend_type: string;
    version: string;
    running: boolean;
};

export type NodeType = z.infer<typeof NodeSchema> & {
    id: number;
    backends: NodeBackendType[];
    // Additional server fields
    xray_version?: string;
    last_status_change?: string; // ISO datetime string
    message?: string; // Up to 1024 characters
    created_at?: string; // ISO datetime string
    uplink?: number; // BigInteger from server
    downlink?: number; // BigInteger from server
    certificate?: string | null; // Text from server
    private_key?: string | null; // Text from server
    cert_created_at?: string | null; // ISO datetime string
    cert_expires_at?: string | null; // ISO datetime string
};
