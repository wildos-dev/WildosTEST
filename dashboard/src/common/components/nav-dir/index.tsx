
import { Link, useRouterState } from "@tanstack/react-router";
import * as React from 'react'
import {
    BreadcrumbPage,
    Drawer,
    DrawerClose,
    DrawerContent,
    DrawerDescription,
    DrawerTrigger,
    Breadcrumb,
    BreadcrumbEllipsis,
    BreadcrumbItem,
    BreadcrumbLink,
    BreadcrumbList,
    BreadcrumbSeparator,
    DrawerFooter,
    DrawerHeader,
    DrawerTitle,
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    Button,
    SidebarObject,
} from "@wildosvpn/common/components"
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import { AppRouterPaths } from "@wildosvpn/common/types";
import { useTranslation } from "react-i18next";

interface Dir {
    href: AppRouterPaths;
    label: string;
}

interface NavigationDirectoryProps {
    sidebar: SidebarObject;
}


function getPathDirs(currentPath: string, sidebar: SidebarObject, t: (key: string) => string): Dir[] {
    const dirs: Dir[] = [];
    const pathArray = currentPath.split('/').filter(Boolean); // Split path and remove empty strings
    let fullPath = '/';
    for (let i = 0; i < pathArray.length; i++) {
        const dir = pathArray[i];
        fullPath += `/${dir}`;
        if (sidebar[dir] && sidebar[dir][0]) {
            dirs.push({ href: sidebar[dir][0].to, label: sidebar[dir][0].title });
        } else {
            dirs.push({ href: fullPath as AppRouterPaths, label: t(dir) });
        }
    }
    return dirs;
}

const ITEMS_TO_DISPLAY = 3

export const NavigationDirectory: React.FC<NavigationDirectoryProps> = ({ sidebar }) => {
    const { t } = useTranslation();
    const [open, setOpen] = React.useState(false)
    const currentPath = useRouterState().location.pathname;
    const items = getPathDirs(currentPath, sidebar, t);
    const isDesktop = !useScreenBreakpoint("sm");
    return (
        <Breadcrumb>
            <BreadcrumbList>
                {items.length > ITEMS_TO_DISPLAY ? (
                    <>
                        <BreadcrumbItem>
                            {isDesktop ? (
                                <DropdownMenu open={open} onOpenChange={setOpen}>
                                    <DropdownMenuTrigger
                                        className="flex gap-1 items-center"
                                        aria-label={t('navigation.toggle-menu')}
                                    >
                                        <BreadcrumbEllipsis className="w-4 h-4" />
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="start">
                                        {items.slice(1, -2).map((item, index) => (
                                            <DropdownMenuItem key={index}>
                                                <Link to={item.href} className="capitalize">
                                                    {item.label}
                                                </Link>
                                            </DropdownMenuItem>
                                        ))}
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            ) : (
                                <Drawer open={open} onOpenChange={setOpen}>
                                    <DrawerTrigger aria-label={t('navigation.toggle-menu-alt')}>
                                        <BreadcrumbEllipsis className="w-4 h-4" />
                                    </DrawerTrigger>
                                    <DrawerContent>
                                        <DrawerHeader className="text-left">
                                            <DrawerTitle>{t('navigation.navigate-to')}</DrawerTitle>
                                            <DrawerDescription>
                                                {t('navigation.select-page-to-navigate')}
                                            </DrawerDescription>
                                        </DrawerHeader>
                                        <div className="grid gap-1 px-4">
                                            {items.slice(1, -2).map((item, index) => (
                                                <Link
                                                    key={index}
                                                    to="/"
                                                    className="py-1 text-sm"
                                                >
                                                    {item.label}
                                                </Link>
                                            ))}
                                        </div>
                                        <DrawerFooter className="pt-4">
                                            <DrawerClose asChild>
                                                <Button variant="outline">{t('close')}</Button>
                                            </DrawerClose>
                                        </DrawerFooter>
                                    </DrawerContent>
                                </Drawer>
                            )}
                        </BreadcrumbItem>
                    </>
                ) : null}
                {items.slice(-ITEMS_TO_DISPLAY + 1).map((item, index) => (
                    <BreadcrumbItem key={index}>
                        {item.href ? (
                            <>
                                <BreadcrumbLink
                                    asChild
                                    className="md:max-w-none max-w-20 truncate text-accent dark:text-accent-foreground hover:text-primary-foreground"
                                >
                                    <Link to={item.href}>{item.label}</Link>
                                </BreadcrumbLink>
                                {index !== items.slice(-ITEMS_TO_DISPLAY + 1).length - 1 && <BreadcrumbSeparator />}
                            </>
                        ) : (
                            <BreadcrumbPage className="md:max-w-none max-w-20 truncate">
                                {item.label}
                            </BreadcrumbPage>
                        )}
                    </BreadcrumbItem>
                ))}
            </BreadcrumbList>
        </Breadcrumb>
    )
}
