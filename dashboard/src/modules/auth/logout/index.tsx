import { Button } from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components";
import * as React from "react";
import { useAuth } from "@wildosvpn/modules/auth";

interface LogoutProps { }

export const Logout: React.FC<LogoutProps> = () => {
    const { removeAllTokens, setSudo } = useAuth();
    
    const handleLogout = React.useCallback(() => {
        // Clear all authentication state (memory + sessionStorage + legacy localStorage)
        removeAllTokens();
        
        // Clear sudo flag from all storages
        setSudo(false);
        
        // Navigate to login page using hash routing
        window.location.hash = '#/login';
    }, [removeAllTokens, setSudo]);
    return (
        <Button
            size="icon"
            variant="ghost"
            onClick={handleLogout}
            className="hstack gap-2 items-center justify-end w-full h-4 p-0"
        >
            Logout
            <Icon name="LogOut" className="size-4" />
        </Button>
    );
};
