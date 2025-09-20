import { OnChangeFn, RowSelectionState } from "@tanstack/react-table"
import * as React from "react";

export interface UseRowSelectionReturn {
    setSelectedRow: OnChangeFn<RowSelectionState>
    selectedRow: RowSelectionState
}

export const useRowSelection = (state: RowSelectionState): UseRowSelectionReturn => {
    const [selectedRow, setSelectedRow] = React.useState<RowSelectionState>(state)
    return { setSelectedRow, selectedRow }
}

