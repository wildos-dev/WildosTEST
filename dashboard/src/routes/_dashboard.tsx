import {
    Header,
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
    Toaster,
    Loading,
    HeaderLogo,
    HeaderMenu,
    Button,
    DashboardSettingsDialog,
} from "@wildosvpn/common/components";
import { useAuth } from "@wildosvpn/modules/auth";
import { DashboardSidebar, ToggleButton } from "@wildosvpn/features/sidebar";
import { usePanelToggle } from "@wildosvpn/features/sidebar/use-panel-toggle";
import { useScreenBreakpoint, useDialog } from "@wildosvpn/common/hooks";
import { cn } from "@wildosvpn/common/utils";
import * as React from "react";
import { Icon } from "@wildosvpn/common/components";
import {
    Outlet,
    Link,
    createFileRoute
} from "@tanstack/react-router";
import { useGithubRepoStatsQuery, GithubRepo } from "@wildosvpn/features/github-repo";
import { CommandBox } from "@wildosvpn/features/search-command";
import { DashboardBottomMenu } from "@wildosvpn/features/bottom-menu";
import { useTranslation } from "react-i18next";

export const DashboardLayout = () => {
    const { t } = useTranslation();
    const isDesktop = useScreenBreakpoint("md");
    const {
        collapsed,
        panelRef,
        setCollapsed,
        toggleCollapse,
    } = usePanelToggle(isDesktop);
    const { isSudo } = useAuth();
    const { data: stats } = useGithubRepoStatsQuery();
    const [settingsOpen, setSettingsOpen] = useDialog(false);

    return (
        <div className="flex flex-col w-screen h-screen bg-slate-900">
            <Header
                start={
                    <>
                        <Link to="/">
                            <HeaderLogo />
                        </Link>
                        {isDesktop && (

                            <ToggleButton
                                collapsed={collapsed}
                                onToggle={toggleCollapse}
                            />
                        )}
                    </>
                }
                center={<CommandBox />}
                end={
                    <>
                        <Button
                            variant="ghost"
                            size="touch-sm"
                            onClick={() => setSettingsOpen(true)}
                            aria-label={t('dashboard_ui.settings-label')}
                            className="mr-1 sm:mr-2"
                        >
                            <Icon name="Settings" className="h-4 w-4 sm:h-5 sm:w-5" />
                        </Button>
                        <GithubRepo {...stats} variant={isDesktop ? "full" : "mini"} />
                        <HeaderMenu />
                    </>
                }
            />
            <div className="flex flex-1 overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
                {isDesktop ? (
                    <ResizablePanelGroup direction="horizontal" className="flex h-full w-full">
                        <ResizablePanel
                            collapsible
                            collapsedSize={2}
                            onCollapse={() => setCollapsed(true)}
                            onExpand={() => setCollapsed(false)}
                            minSize={15}
                            className={cn("w-[120px] min-w-[70px]")}
                            defaultSize={20}
                            ref={panelRef}
                            maxSize={30}
                        >
                            <DashboardSidebar
                                collapsed={collapsed}
                                setCollapsed={setCollapsed}
                            />
                        </ResizablePanel>
                        <ResizableHandle withHandle className="w-[2px]" />
                        <ResizablePanel className="flex flex-col h-full">
                            <main className="flex-grow flex flex-col overflow-y-auto">
                                <React.Suspense fallback={<Loading />}>
                                    <Outlet />
                                </React.Suspense>
                            </main>
                        </ResizablePanel>
                    </ResizablePanelGroup>
                ) : (
                    <div className="flex flex-col h-full w-full">
                        <main className="flex flex-col h-full overflow-y-auto">
                            <React.Suspense fallback={<Loading />}>
                                <Outlet />
                            </React.Suspense>
                            <footer className="h-30 border-t-3 shrink-0 py-2 px-5 pb-[env(safe-area-inset-bottom)]">
                                <DashboardBottomMenu variant={isSudo() ? "sudo-admin" : "admin"} />
                            </footer>
                        </main>
                    </div>
                )}
            </div>
            <Toaster position="top-center" />
            <DashboardSettingsDialog
                open={settingsOpen}
                onOpenChange={setSettingsOpen}
            />
        </div>
    );
};

export const Route = createFileRoute("/_dashboard")({
    component: () => <DashboardAuthGuard />,
});

// Auth guard component that handles authentication check
const DashboardAuthGuard = () => {
    const [isChecking, setIsChecking] = React.useState(true);
    const [isLoggedIn, setIsLoggedIn] = React.useState(false);

    React.useEffect(() => {
        const checkAuth = async () => {
            try {
                const loggedIn = await useAuth.getState().isLoggedIn();
                if (!loggedIn) {
                    // Use hash routing for login redirect
                    window.location.hash = '#/login';
                    return;
                }
                setIsLoggedIn(true);
            } catch (error) {
                window.location.hash = '#/login';
            } finally {
                setIsChecking(false);
            }
        };

        checkAuth();
    }, []);

    if (isChecking) {
        return <Loading />;
    }

    if (!isLoggedIn) {
        return null; // Will redirect via useEffect
    }

    return <DashboardLayout />;
};
