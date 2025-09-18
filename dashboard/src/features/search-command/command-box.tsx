import * as React from "react";
import {
    CommandDialog,
    CommandEmpty,
    CommandInput,
    CommandList,
    ScrollArea,
} from "@wildosvpn/common/components";
import { SearchBox } from "./search-box";
import { useAuth } from "@wildosvpn/modules/auth";
import { CommandItems } from "./command-items";
import { commandItems } from "./commands";
import { useTranslation } from "react-i18next";

export function CommandBox() {
    const [open, setOpen] = React.useState(false);
    const { isSudo } = useAuth();
    const { t } = useTranslation();

    React.useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((open) => !open);
            }
        };
        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    return (
        <>
            <SearchBox onClick={() => setOpen(true)} />
            <CommandDialog open={open} onOpenChange={setOpen}>
                <CommandInput
                    placeholder={t("placeholders.type-to-search")}
                    className="focus:ring-0 ring-0 m-1 border-none"
                />
                <ScrollArea className="max-h-100">
                    <CommandList>
                        <CommandEmpty>{t("features.search.no-results-found")}</CommandEmpty>
                        <CommandItems items={commandItems} isSudo={isSudo} setOpen={setOpen} />
                    </CommandList>
                </ScrollArea>
            </CommandDialog>
        </>
    );
}


