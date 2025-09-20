import { OnChangeFn, SortingState } from "@tanstack/react-table"
import * as React from "react"

export interface UseSortingReturn {
    sorting: SortingState
    setSorting: OnChangeFn<SortingState>
}

export const useSorting = () => {
    const [sorting, setSorting] = React.useState<SortingState>([])
    return { sorting, setSorting }
}
