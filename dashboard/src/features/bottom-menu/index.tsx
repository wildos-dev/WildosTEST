import { Button, SidebarItem } from "@wildosvpn/common/components";
import { Link } from "@tanstack/react-router";
import * as React from "react";
import { Icon } from '@wildosvpn/common/components';
import { useIsCurrentRoute } from "@wildosvpn/common/hooks";
import { cn } from "@wildosvpn/common/utils";
import { useTranslation } from "react-i18next";

type BottomMenuItemProps = Omit<SidebarItem, 'isParent' | 'subItem'>

const BottomMenuItem: React.FC<BottomMenuItemProps & { active: boolean; compact?: boolean }> = ({ title, icon, to, active, compact = false }) => {
    return (
        <Button 
            asChild 
            variant={active ? "default" : "ghost"} 
            className={cn(
                "gap-1 flex flex-col justify-center text-xs h-full py-1",
                compact 
                    ? "size-12 sm:size-14 text-[10px] sm:text-xs" 
                    : "size-14 py-2"
            )}
        >
            <Link to={to} className="flex flex-col items-center justify-center gap-0.5 sm:gap-1">
                <div className={cn("shrink-0", compact ? "[&>svg]:h-4 [&>svg]:w-4 sm:[&>svg]:h-5 sm:[&>svg]:w-5" : "[&>svg]:h-5 [&>svg]:w-5")}>
                    {icon}
                </div>
                <span className={cn("truncate leading-tight", compact && "hidden xs:block")}>{title}</span>
            </Link>
        </Button>
    )
}

export const DashboardBottomMenu = ({ variant = "admin" }: { variant: "sudo-admin" | "admin" }) => {
    const { isCurrentRouteActive } = useIsCurrentRoute()
    const { t } = useTranslation()
    
    const adminItems: BottomMenuItemProps[] = [
        {
            title: t('users'),
            to: '/users',
            icon: <Icon name="Users" />,
        },
        {
            title: t('home'),
            to: '/',
            icon: <Icon name="Home" />,
        },
    ]

    const sudoAdminItems: BottomMenuItemProps[] = [
        {
            title: t('users'),
            to: '/users',
            icon: <Icon name="Users" />,
        },
        {
            title: t('services'),
            to: '/services',
            icon: <Icon name="Server" />,
        },
        {
            title: t('home'),
            to: '/',
            icon: <Icon name="Home" />,
        },
        {
            title: t('nodes'),
            to: '/nodes',
            icon: <Icon name="Box" />,
        },
        {
            title: t('hosts'),
            to: '/hosts',
            icon: <Icon name="ServerCog" />,
        },
    ]
    
    const items = variant === "sudo-admin" ? sudoAdminItems : adminItems;
    const isCompact = variant === "sudo-admin";
    
    return (
        <div className={cn(
            "w-full flex flex-row items-center px-1 sm:px-2", 
            variant === "admin" 
                ? "justify-evenly" 
                : "justify-between gap-1 sm:gap-2"
        )}>
            {items.map((item: BottomMenuItemProps) => (
                <BottomMenuItem
                    key={item.to}
                    active={isCurrentRouteActive(item.to)}
                    compact={isCompact}
                    {...item}
                />
            ))}
        </div>
    )
}

