import * as React from "react";
import { AdminType } from "@wildosvpn/modules/admins";

interface RouterAdminContextProps {
    admin: AdminType | null;
    isPending?: boolean;
}

export const RouterAdminContext = React.createContext<RouterAdminContextProps | null>(null);

export const useRouterAdminContext = () => {
    const ctx = React.useContext(RouterAdminContext);
    return ctx;
};
