import * as React from "react";
import { UserType } from "@wildosvpn/modules/users";

interface RouterUserContextProps {
    user: UserType | null;
    isPending?: boolean;
}

export const RouterUserContext = React.createContext<RouterUserContextProps | null>(null);

export const useRouterUserContext = () => {
    const ctx = React.useContext(RouterUserContext);
    return ctx;
};
