import { cn } from "@wildosvpn/common/utils"
import * as React from 'react'

export interface SidebarHeaderProps extends
    React.PropsWithChildren,
    React.HTMLAttributes<HTMLLinkElement> { }

export const SidebarHeader: React.FC<SidebarHeaderProps> = ({ children, className }) => {
    return (
        <div className={cn(className)}>{children}</div>
    )
}
