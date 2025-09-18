import * as React from "react";
import { ServiceType } from "@wildosvpn/modules/services";

interface RouterServiceContextProps {
    service: ServiceType;
}

export const RouterServiceContext = React.createContext<RouterServiceContextProps | null>(null);

export const useRouterServiceContext = () => {
    const ctx = React.useContext(RouterServiceContext);
    return ctx;
};
