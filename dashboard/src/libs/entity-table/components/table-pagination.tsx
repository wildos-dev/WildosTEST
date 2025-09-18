import {
    Button,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { Table } from "@tanstack/react-table"
import { useLocalStorage } from "@uidotdev/usehooks";
import { useEntityTableContext } from "../contexts";

export function DataTablePagination<TData>({ table }: { table: Table<TData> }) {
    const { t } = useTranslation();
    const { entityKey } = useEntityTableContext();
    const [,setRowPerPageLocal] = useLocalStorage<number>(`wildosvpn-table-row-per-page-${entityKey}`, 10);

    // Show pagination only if there are multiple pages
    if (table.getPageCount() <= 1) {
        return null;
    }

    return (
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between p-4">
            {/* Row selection info - show on desktop only */}
            {table.options.onRowSelectionChange && (
                <div className="text-sm text-muted-foreground">
                    {table.getFilteredSelectedRowModel().rows.length} / {table.getFilteredRowModel().rows.length} {t("table.selected")}
                </div>
            )}

            {/* Centered pagination - NodesGrid style */}
            <div className="flex justify-center flex-1">
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                    >
                        {t('navigation.previous') || 'Previous'}
                    </Button>
                    <span className="text-sm text-muted-foreground px-4">
                        {t("pagination.page")} {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
                    </span>
                    <Button
                        variant="outline"
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                    >
                        {t('navigation.next') || 'Next'}
                    </Button>
                </div>
            </div>

            {/* Rows per page selector - compact version for mobile */}
            <div className="flex items-center gap-2">
                <span className="text-sm font-medium hidden sm:inline">
                    {t("table.row-per-page")}
                </span>
                <Select
                    value={`${table.getState().pagination.pageSize}`}
                    onValueChange={(value) => {
                        table.setPageSize(Number(value));
                        table.setPageIndex(0);
                        setRowPerPageLocal(Number(value));
                    }}
                >
                    <SelectTrigger className="h-8 w-[70px]">
                        <SelectValue placeholder={table.getState().pagination.pageSize} />
                    </SelectTrigger>
                    <SelectContent side="top">
                        {[10, 20, 50, 100].map((pageSize) => (
                            <SelectItem key={pageSize} value={`${pageSize}`}>
                                {pageSize}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
        </div>
    );
}
