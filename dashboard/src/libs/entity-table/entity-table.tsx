import * as React from "react";
import { Button } from "@wildosvpn/common/components";
import { DataTableViewOptions } from "./components";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { EntityTableContext } from "./contexts";
import { TableSearch, DataTablePagination, EntityDataTable } from "./components";
import {
    usePrimaryFiltering,
    usePagination,
    useEntityTable,
    useVisibility,
    useSorting,
    type UseRowSelectionReturn,
    type FetchEntityReturn,
    type QueryKey,
    type EntityQueryKeyType,
    useFilters,
} from "./hooks";

export interface EntityTableProps<T> {
    columns: ColumnDef<T>[];
    primaryFilter: string;
    entityKey: string;
    rowSelection?: UseRowSelectionReturn;
    fetchEntity: ({ queryKey }: EntityQueryKeyType) => FetchEntityReturn<T>;
    onCreate?: () => void;
    onOpen?: (entity: any) => void;
    CardComponent?: React.ComponentType<{ 
        entity: T;
        actions: any;
        onRowClick?: (entity: T) => void;
    }>;
    cardActions?: any;
}

export function EntityTable<T>({
    fetchEntity,
    columns,
    primaryFilter,
    rowSelection,
    entityKey,
    onCreate,
    onOpen,
    CardComponent,
    cardActions,
}: EntityTableProps<T>) {
    const { t } = useTranslation();
    const columnPrimaryFilter = usePrimaryFiltering({ column: primaryFilter });
    const filters = useFilters();
    const sorting = useSorting();
    const visibility = useVisibility();
    const { onPaginationChange, pageIndex, pageSize } = usePagination({ entityKey });

    const query: QueryKey = [
        entityKey,
        {
            page: pageIndex,
            size: pageSize,
        },
        columnPrimaryFilter.columnFilters,
        {
            sortBy: sorting.sorting[0]?.id || "created_at",
            desc: sorting.sorting[0]?.desc ?? true,
        },
        { filters: filters.columnsFilter }
    ];

    const { data, isFetching, error, isError, refetch } = useQuery({
        queryFn: fetchEntity,
        queryKey: query,
        initialData: { entities: [], pageCount: 0 },
    });

    const table = useEntityTable({
        data,
        columns,
        pageSize,
        pageIndex,
        rowSelection,
        visibility,
        sorting,
        onPaginationChange,
    });

    const contextValue = React.useMemo(
        () => ({ 
            entityKey, 
            table, 
            data: data.entities, 
            primaryFilter: columnPrimaryFilter, 
            filters, 
            isLoading: isFetching,
            error: error || null,
            isError,
            refetch
        }),
        [entityKey, table, data.entities, filters, columnPrimaryFilter, isFetching, error, isError, refetch],
    );

    return (
        <EntityTableContext.Provider value={contextValue}>
            <div className="flex w-full flex-col">
                <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between py-4">
                    <div className="flex flex-col sm:flex-row gap-4 flex-1">
                        <TableSearch />
                        <DataTableViewOptions table={table} />
                    </div>
                    {onCreate && (
                        <Button 
                            aria-label={`create-${entityKey}`} 
                            onClick={onCreate}
                            className="shrink-0"
                        >
                            {t("create")}
                        </Button>
                    )}
                </div>
                <div className="w-full rounded-md border">
                    <EntityDataTable 
                        columns={columns} 
                        onRowClick={onOpen} 
                        CardComponent={CardComponent}
                        cardActions={cardActions}
                    />
                    <DataTablePagination table={table} />
                </div>
            </div>
        </EntityTableContext.Provider>
    );
}
