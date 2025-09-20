import { z } from "zod";
import { ProtocolType } from "@wildosvpn/modules/inbounds";

export const HostSchema = z.object({
    remark: z.string().min(1, "validation.hosts.remark_required"),
    address: z.string().min(1, "validation.hosts.address_required"),
    is_disabled: z.boolean().default(false),
    weight: z.coerce
        .number().int()
        .nullable()
        .optional(),
    port: z
        .preprocess(
            (val) => (val === "" || val === undefined || val === null ? null : Number(val)),
            z.union([
                z
                    .number()
                    .int()
                    .gte(1, "validation.hosts.port_min")
                    .lte(65535, "validation.hosts.port_max"),
                z.null(),
            ])
        ),
});


export type HostSchemaType = z.infer<typeof HostSchema>;
export type HostType = HostSchemaType & { id?: number, inboundId?: number, protocol: ProtocolType };
