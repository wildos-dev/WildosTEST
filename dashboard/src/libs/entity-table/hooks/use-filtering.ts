import { OnChangeFn } from "@tanstack/react-table"
import * as React from "react"

export interface UseFiltersReturn {
    columnsFilter: Record<string, string | undefined>
    setColumnsFilter: OnChangeFn<Record<string, string | undefined>>
}

export const useFilters = (): UseFiltersReturn => {
    const [columnsFilter, setColumnsFilter] = React.useState<Record<string, string | undefined>>({})
    return { columnsFilter, setColumnsFilter }
}
