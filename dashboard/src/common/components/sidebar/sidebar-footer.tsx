import * as React from 'react'

export interface SidebarFooterProps
    extends React.PropsWithChildren {
}


export const SidebarFooter: React.FC<SidebarFooterProps> = ({children}) => {
    return (
        <div>{children}</div>
    )
}
