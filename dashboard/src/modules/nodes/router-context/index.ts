import * as React from "react";
import { NodeType } from "@wildosvpn/modules/nodes";

interface RouterNodeContextProps {
    node: NodeType;
}

export const RouterNodeContext = React.createContext<RouterNodeContextProps | null>(null);

export const useRouterNodeContext = () => {
    const ctx = React.useContext(RouterNodeContext);
    return ctx;
};
