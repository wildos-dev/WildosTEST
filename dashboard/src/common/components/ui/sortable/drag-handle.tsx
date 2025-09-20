import * as React from 'react';
import { Button, type ButtonProps } from "@wildosvpn/common/components"
import { useSortableItem } from "./use-sortable-item";
import { composeRefs, cn } from "@wildosvpn/common/utils";
import { useTranslation } from "react-i18next";

interface SortableDragHandleProps extends ButtonProps {
    withHandle?: boolean
}

export const SortableDragHandle = React.forwardRef<
    HTMLButtonElement,
    SortableDragHandleProps
>(({ className, ...props }, ref) => {
    const { t } = useTranslation();
    const { attributes, listeners } = useSortableItem()

    return (
        <Button
            ref={composeRefs(ref)}
            className={cn("cursor-grab", className)}
            aria-roledescription={t('accessibility.draggable')}
            aria-label={t('accessibility.drag_to_reorder')}
            {...attributes}
            {...listeners}
            {...props}
        />
    )
})
SortableDragHandle.displayName = "SortableDragHandle"
