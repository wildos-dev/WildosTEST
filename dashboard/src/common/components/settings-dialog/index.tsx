import * as React from "react";
import {
    ScrollArea,
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";

export interface SettingsDialogProps {
    onOpenChange: (state: boolean) => void;
    open: boolean;
    onClose?: () => void;
}

export const SettingsDialog: React.FC<SettingsDialogProps & React.PropsWithChildren> = ({
    open,
    onOpenChange,
    children,
    onClose = () => null,
}) => {
    const { t } = useTranslation();

    return (
        <Sheet open={open} onOpenChange={(state) => { if (!state) onClose(); onOpenChange(state); }}>
            <SheetContent 
                side="right"
                className="w-full h-dvh sm:w-full sm:h-dvh md:max-w-[840px] lg:max-w-[960px] md:h-[90dvh] space-y-5"
            >
                <SheetHeader>
                    <SheetTitle>{t("settings")}</SheetTitle>
                    <SheetDescription>
                        {t("page.settings.description")}
                    </SheetDescription>
                </SheetHeader>
                <ScrollArea className="flex flex-col gap-4 h-[calc(100dvh-120px)] md:h-[calc(90dvh-120px)] max-h-full">
                    {children}
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
};
