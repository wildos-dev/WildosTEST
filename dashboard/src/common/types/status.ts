import { BadgeVariantKeys } from "@wildosvpn/common/components";
import { ElementType } from "react";

export interface StatusType {
    label: string;
    icon: ElementType | null;
    variant?: BadgeVariantKeys | undefined
}
