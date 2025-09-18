import * as React from "react";
import { HostType } from "@wildosvpn/modules/hosts";

interface RouterHostContextProps {
    host: HostType;
}

export const RouterHostContext = React.createContext<RouterHostContextProps | null>(null);

export const useRouterHostContext = () => {
    const ctx = React.useContext(RouterHostContext);
    return ctx;
};
