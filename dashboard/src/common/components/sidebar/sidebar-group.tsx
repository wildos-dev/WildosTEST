
import * as React from 'react'
import { Label } from "@wildosvpn/common/components"
import { cn } from "@wildosvpn/common/utils"
import { useSidebarContext } from "./sidebar-provider";

export interface SidebarGroupProps
    extends React.PropsWithChildren {
    className: string
}

export const SidebarGroup: React.FC<SidebarGroupProps> = ({ children, className }) => {
    const { collapsed } = useSidebarContext();

    if (!collapsed)
        return (
            <Label className={cn(className, "text-gray-500 font-header")}>
                {children}
            </Label>
        )
}
