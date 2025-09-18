import { Row } from "@tanstack/react-table"
import * as React from 'react'
import {
    type ColumnActions
} from "@wildosvpn/libs/entity-table";

interface NoPropogationButtonProps<T> {
    actions: ColumnActions<T>,
    row: Row<T>,
}

export function NoPropogationButton<T>({ children, actions, row }: NoPropogationButtonProps<T> & React.PropsWithChildren) {
    const handleKeyDown = React.useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            e.stopPropagation();
            if (actions?.onOpen && row?.original) {
                actions.onOpen(row.original);
            }
        }
    }, [actions, row]);

    return (
        <div
            className="flex flex-row gap-2 items-center"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={handleKeyDown}
            tabIndex={0}
            role="button"
        >
            {children}
        </div>
    )
}

