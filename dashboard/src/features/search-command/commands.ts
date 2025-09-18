import { ElementType } from "react";
import { 
    Users,
    Server,
    Box,
    ServerCog,
    Settings,
    Shield
} from "@wildosvpn/common/components/ui/icon/CommonIcons";

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
                icon: Users,
                label: "users",
                path: "/users",
                sudo: false,
            },
            {
                icon: Server,
                label: "services",
                path: "/services",
                sudo: true,
            },
            {
                icon: Box,
                label: "nodes",
                path: "/nodes",
                sudo: true,
            },
            {
                icon: ServerCog,
                label: "hosts",
                path: "/hosts",
                sudo: true,
            },
            {
                icon: Shield,
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
                icon: Users,
                label: "page.users.dialogs.creation.title",
                path: "/users/create",
                sudo: false,
            },
            {
                icon: Server,
                label: "page.services.dialogs.creation.title",
                path: "/services/create",
                sudo: true,
            },
            {
                icon: Box,
                label: "page.nodes.dialogs.creation.title",
                path: "/nodes/create",
                sudo: true,
            },
            {
                icon: Shield,
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
                icon: Settings,
                label: "settings",
                path: "/settings",
                sudo: true,
            },
        ],
    },
];
