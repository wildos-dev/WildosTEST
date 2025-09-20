import { AppRouterPaths } from "@wildosvpn/common/types";
import * as React from "react";

export interface SidebarItem {
    title: string;
    to: AppRouterPaths;
    icon: React.ReactNode;
    isParent: boolean;
    subItem?: SidebarItem[];
}

export interface SidebarObject {
    [key: string]: SidebarItem[];
}

export type SidebarItemGroup = Record<string, SidebarItem[]>;
