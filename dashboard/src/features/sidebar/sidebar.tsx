import {
    Sidebar,
    type SidebarItem,
} from "@wildosvpn/common/components";
import { useIsCurrentRoute } from "@wildosvpn/common/hooks";
import * as React from 'react';
import { useSidebarItems } from "./items";
import { cn } from "@wildosvpn/common/utils";
import { useAuth } from "@wildosvpn/modules/auth";

interface DashboardSidebarProps {
    collapsed: boolean;
    setCollapsed: (state: boolean) => void;
    open?: boolean;
    setOpen?: (state: boolean) => void;
}

export const DashboardSidebar: React.FC<DashboardSidebarProps> = ({
    collapsed,
    setCollapsed,
    setOpen,
    open,
}) => {
    const { isSudo } = useAuth();
    const { isCurrentRouteActive } = useIsCurrentRoute();
    const { sidebarItems: sidebarItemsSudoAdmin, sidebarItemsNonSudoAdmin } = useSidebarItems();
    const sidebarItems = isSudo() ? sidebarItemsSudoAdmin : sidebarItemsNonSudoAdmin
    return (
        <aside className="size-full py-4  px-4 ">
            <nav className="size-full">
                <Sidebar
                    sidebar={sidebarItems}
                    collapsed={collapsed}
                    setCollapsed={setCollapsed}
                    open={open}
                    setOpen={setOpen}
                >
                    <div className="flex size-full flex-col justify-between">
                        <Sidebar.Body>
                            {Object.keys(sidebarItems).map((key) => (
                                <div className="w-full" key={key}>
                                    <Sidebar.Group className="uppercase">{key}</Sidebar.Group>
                                    {sidebarItems[key].map((item: SidebarItem) => (
                                        <Sidebar.Item
                                            variant={isCurrentRouteActive(item.to) ? "active" : "default"}
                                            className={cn("my-2 border-transparent", {
                                                "w-10 h-10": collapsed,
                                            })}
                                            item={item}
                                            key={item.title}
                                        />
                                    ))}
                                </div>
                            ))}
                        </Sidebar.Body>
                    </div>
                </Sidebar>
            </nav>
        </aside>
    );
};
