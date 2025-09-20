import { OnChangeFn, VisibilityState } from "@tanstack/react-table"
import * as React from "react"

export interface UseVisibilityReturn {
    columnVisibility: VisibilityState
    setColumnVisibility: OnChangeFn<VisibilityState>
}

export const useVisibility = () => {
    const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
    return { columnVisibility, setColumnVisibility }
}
