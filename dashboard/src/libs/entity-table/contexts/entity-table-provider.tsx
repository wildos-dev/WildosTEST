import * as React from "react";
import { UseFiltersReturn, UsePrimaryFilterReturn } from "../hooks";
import { Table } from "@tanstack/react-table";

interface EntityTableContextProps<TData> {
    entityKey: string
    table: Table<TData>
    data: TData[]
    primaryFilter: UsePrimaryFilterReturn
    filters: UseFiltersReturn
    isLoading: boolean
    error: Error | null
    isError: boolean
    refetch?: () => void
}

// Safe createContext with fallback
export const EntityTableContext = (React?.createContext || (() => {
    throw new Error("React is not available - check React imports and build configuration");
}))<EntityTableContextProps<any> | null>(null);

export const useEntityTableContext = () => {
    const ctx = (React?.useContext || (() => {
        throw new Error("React is not available - check React imports and build configuration");
    }))(EntityTableContext);
    if (!ctx)
        throw new Error('EntityTable.* component must be rendered as child of EntityTable');
    return ctx;
}
