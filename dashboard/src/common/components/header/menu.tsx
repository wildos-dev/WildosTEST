import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
    DropdownMenuGroup,
    Button,
} from "@wildosvpn/common/components";
import { Link } from "@tanstack/react-router";
import * as React from 'react';
import { Icon } from "@wildosvpn/common/components";
import { LanguageSwitchMenu } from "@wildosvpn/features/language-switch";
import { useAuth, Logout } from "@wildosvpn/modules/auth";
import { useScreenBreakpoint } from "@wildosvpn/common/hooks/use-screen-breakpoint";
import { useTranslation } from "react-i18next";
import { VersionIndicator } from "@wildosvpn/features/version-indicator";

export const HeaderMenu: React.FC = () => {

    const isDesktop = useScreenBreakpoint("md");
    const { isSudo } = useAuth();
    const { t } = useTranslation();

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="secondary"
                    className="bg-slate-800/80 border border-slate-700/50 text-slate-200 hover:bg-slate-700/80 hover:text-white transition-all duration-200"
                    size="icon"
                    aria-label={t('navigation.menu-button')}
                >
                    <Icon name="Menu" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
                <DropdownMenuLabel>{t('navigation.menu')}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {(!isDesktop && isSudo()) && (
                    <>
                        <DropdownMenuItem className="w-full">
                            <Link to="/settings" className="hstack gap-1 items-center justify-between w-full h-fit p-0">
                                {t("settings")}
                                <Icon name="Settings" className="size-4" />
                            </Link>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="w-full">
                            <Link to="/admins" className="hstack gap-1 items-center justify-between w-full h-fit p-0" >
                                {t("admins")}
                                <Icon name="ShieldCheck" className="size-4" />
                            </Link>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                    </>
                )}
                <DropdownMenuItem className="w-full">
                    <Logout />
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuGroup>
                    <LanguageSwitchMenu />
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuGroup className="py-1 shrink-0">
                    <VersionIndicator />
                </DropdownMenuGroup>
            </DropdownMenuContent>
        </DropdownMenu >
    )
};
