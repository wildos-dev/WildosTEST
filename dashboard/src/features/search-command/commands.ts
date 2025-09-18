import { ElementType } from "react";
import { CommonIcons } from "@wildosvpn/common/components/ui/icon";

export interface CommandItemConfig {
    icon: ElementType;
    label: string;
    path: string;
    sudo: boolean;
}

export interface CommandGroupConfig {
    group: string;
    items: CommandItemConfig[];
}

export const commandItems: CommandGroupConfig[] = [
    {
        group: "features.search.groups.pages",
        items: [
            {
                icon: CommonIcons.Users,
                label: "users",
                path: "/users",
                sudo: false,
            },
            {
                icon: CommonIcons.Server,
                label: "services",
                path: "/services",
                sudo: true,
            },
            {
                icon: CommonIcons.Box,
                label: "nodes",
                path: "/nodes",
                sudo: true,
            },
            {
                icon: CommonIcons.ServerCog,
                label: "hosts",
                path: "/hosts",
                sudo: true,
            },
            {
                icon: CommonIcons.Shield,
                label: "admins",
                path: "/admins",
                sudo: true,
            },
        ],
    },
    {
        group: "features.search.groups.actions",
        items: [
            {
                icon: CommonIcons.Users,
                label: "page.users.dialogs.creation.title",
                path: "/users/create",
                sudo: false,
            },
            {
                icon: CommonIcons.Server,
                label: "page.services.dialogs.creation.title",
                path: "/services/create",
                sudo: true,
            },
            {
                icon: CommonIcons.Box,
                label: "page.nodes.dialogs.creation.title",
                path: "/nodes/create",
                sudo: true,
            },
            {
                icon: CommonIcons.Shield,
                label: "page.admins.dialogs.creation.title",
                path: "/admins/create",
                sudo: true,
            },
        ],
    },
    {
        group: "features.search.groups.settings",
        items: [
            {
                icon: CommonIcons.Settings,
                label: "settings",
                path: "/settings",
                sudo: true,
            },
        ],
    },
];
