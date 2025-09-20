import { cn } from "@wildosvpn/common/utils"
import * as React from 'react'

export interface SidebarBodyProps
    extends React.PropsWithChildren,
    React.HTMLAttributes<HTMLUListElement> { }

export const SidebarBody: React.FC<SidebarBodyProps> = ({ children, className }) => {
    return (
        <ul className={cn(className, "flex flex-col justify-center items-start w-full")}>
            {children}
        </ul>
    )
}
