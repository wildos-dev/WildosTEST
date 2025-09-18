import { useAuth } from "@wildosvpn/modules/auth";
import * as React from "react";

export const SudoRoute: React.FC<React.PropsWithChildren> = ({ children }) => {
    const { isSudo, isLoggedIn } = useAuth();

    React.useEffect(() => {
        const checkAccess = async () => {
            const loggedIn = await isLoggedIn();
            if (!loggedIn || !isSudo()) {
                // Use hash routing for login redirect - consistent with other auth guards
                window.location.hash = '#/login';
            }
        };

        checkAccess();
    }, [isSudo, isLoggedIn]);

    if (!isSudo) {
        return null; 
    }

    return children;
};

