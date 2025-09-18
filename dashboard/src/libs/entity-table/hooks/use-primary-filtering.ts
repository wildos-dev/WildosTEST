import { OnChangeFn } from "@tanstack/react-table"
import * as React from "react"

export interface UsePrimaryFilterType {
    column: string
}

export interface UsePrimaryFilterReturn extends UsePrimaryFilterType {
    columnFilters: string
    setColumnFilters: OnChangeFn<string>
}

export const usePrimaryFiltering = ({ column }: UsePrimaryFilterType): UsePrimaryFilterReturn => {
    const [columnFilters, setColumnFilters] = React.useState<string>("")
    
    // Runtime guard to ensure primaryFilter is always a string
    const safeSetColumnFilters: OnChangeFn<string> = React.useCallback((valueOrUpdater) => {
        setColumnFilters((prev) => {
            const newValue = typeof valueOrUpdater === 'function' ? valueOrUpdater(prev) : valueOrUpdater;
            // Coerce to string to prevent objects/events from corrupting queryKey
            return typeof newValue === 'string' ? newValue : String(newValue || '');
        });
    }, []);
    
    return { setColumnFilters: safeSetColumnFilters, columnFilters, column }
}
