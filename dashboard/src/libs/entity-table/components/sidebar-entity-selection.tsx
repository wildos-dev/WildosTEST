import {
    ToggleGroup, ToggleGroupItem,
    Table, TableHeader, TableRow, TableBody, TableHead,
    ScrollArea, Button,
} from "@wildosvpn/common/components";
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import { cn } from "@wildosvpn/common/utils";
import {
    SidebarEntityCard,
} from "@wildosvpn/libs/entity-table/components";
import {
    useEntityTableContext,
    useSidebarEntityTableContext
} from "@wildosvpn/libs/entity-table/contexts";
import { useTranslation } from "react-i18next";

export const SidebarEntitySelection = () => {
    const sidebarContext = useSidebarEntityTableContext();
    const entityContext = useEntityTableContext();
    
    if (!sidebarContext || !entityContext) return null;
    
    const {
        sidebarEntityId,
        sidebarEntities,
        setSidebarEntityId,
        sidebarCardProps,
    } = sidebarContext;
    const { table } = entityContext;
    const isDesktop = useScreenBreakpoint("md");

    const scrollBarHeight = (table.getState().pagination.pageSize <= 10 && isDesktop) ? "max-h-[45rem]" : "max-h-[20rem]"
    const { t } = useTranslation();

    return (
        <Table className="w-full">
            <TableHeader>
                <TableRow>
                    <TableHead className="hstack justify-between items-center">
                        {t("inbounds")}
                        <Button
                            variant="ghost"
                            size="sm"
                            className="p-1"
                            onMouseDown={() => setSidebarEntityId(undefined)}
                        >
                            {t('deselect')}
                        </Button>
                    </TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                <ToggleGroup
                    type="single"
                    onValueChange={(value) => setSidebarEntityId(value === "" ? undefined : value)}
                    defaultValue={sidebarEntityId ? String(sidebarEntityId) : undefined}
                >
                    <ScrollArea className={cn("flex flex-col justify-start p-1 gap-3 h-full w-full", scrollBarHeight)}>
                        {sidebarEntities.map((entity: any) => (
                            <ToggleGroupItem
                                className="px-0 w-full h-30"
                                value={String(entity.id)}
                                key={String(entity.id)}
                                id={String(entity.id)}>
                                <SidebarEntityCard
                                    {...(sidebarCardProps || {})}
                                    entity={entity}
                                    checked={sidebarEntityId === String(entity.id)}
                                />
                            </ToggleGroupItem>
                        ))}
                    </ScrollArea>
                </ToggleGroup>
            </TableBody>
        </Table>
    )
}
