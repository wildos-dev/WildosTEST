import { TooltipProvider, Loading } from '@wildosvpn/common/components';
import { ThemeProvider } from '@wildosvpn/features/theme-switch'
import { queryClient } from '@wildosvpn/common/utils';
import { QueryClientProvider } from '@tanstack/react-query';
import { createRootRoute, Outlet } from '@tanstack/react-router'
import * as React from 'react'
import { useAuth } from '@wildosvpn/modules/auth'

// Auth initializer component
const AuthInitializer = ({ children }: { children: React.ReactNode }) => {
    const { initializeFromSession, getAuthToken, setSudo } = useAuth();
    
    React.useEffect(() => {
        // Initialize auth tokens from sessionStorage on app startup
        initializeFromSession();
        
        // Security check: Clear stale sudo state if no auth token
        const token = getAuthToken();
        if (!token) {
            // If no token but sessionStorage has is-sudo, clear it to prevent stale sudo state
            if (sessionStorage.getItem('is-sudo')) {
                setSudo(false);
            }
        }
    }, [initializeFromSession, getAuthToken, setSudo]);
    
    return <>{children}</>;
};

export const Route = createRootRoute({
    component: () => (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider>
                <TooltipProvider>
                    <AuthInitializer>
                        <React.Suspense fallback={<Loading />}>
                            <Outlet />
                        </React.Suspense>
                    </AuthInitializer>
                </TooltipProvider>
            </ThemeProvider>
        </QueryClientProvider>
    ),
})
