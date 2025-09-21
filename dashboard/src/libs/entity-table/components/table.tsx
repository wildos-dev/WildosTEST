import {
    ColumnDef,
    flexRender,
} from "@tanstack/react-table";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
    Skeleton,
    Button,
    ScrollableTable
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { useEntityTableContext } from "@wildosvpn/libs/entity-table/contexts";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import * as React from "react";

interface DataTableProps<TData, TValue> {
    columns: ColumnDef<TData, TValue>[]
    onRowClick?: (object: TData) => void
    CardComponent?: React.ComponentType<{ 
        entity: TData;
        actions: any;
        onRowClick?: (entity: TData) => void;
    }>
    cardActions?: any
}

const Headers = () => {
    const context = useEntityTableContext();
    if (!context) return null;
    
    const { table } = context;
    return (
        table.getHeaderGroups().map(headerGroup => (
            <TableRow key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                    <TableHead key={header.id}>
                        {!header.isPlaceholder && flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                ))}
            </TableRow>
        ))
    )
};

const Rows: React.FC<Readonly<DataTableProps<any, any>>> = ({
    columns,
    onRowClick
}) => {
    const context = useEntityTableContext();
    const { t } = useTranslation();
    
    if (!context) {
        return (
            <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                    {t('table.no-result')}
                </TableCell>
            </TableRow>
        );
    }
    
    const { table } = context;

    const rowModel = table?.getRowModel();
    const rows = rowModel?.rows;

    return (rows?.length ? (
        rows.map(row => (
            <TableRow
                key={row.id}
                data-state={row.getIsSelected() ? "selected" : undefined}
                data-testid="entity-table-row"
                onClick={() => onRowClick?.(row.original)}
                className="group hover:bg-muted/50 cursor-pointer"
            >
                {row.getVisibleCells().map(cell => (
                    <TableCell key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                ))}
            </TableRow>
        ))
    ) : (
        <TableRow>
            <TableCell colSpan={columns.length} className="h-24 text-center">
                {t('table.no-result')}
            </TableCell>
        </TableRow>
    ))
};

const Cards: React.FC<Readonly<DataTableProps<any, any>>> = ({
    onRowClick,
    CardComponent,
    cardActions
}) => {
    const context = useEntityTableContext();
    const { t } = useTranslation();
    
    if (!context) {
        return (
            <div className="flex items-center justify-center h-24 text-center text-muted-foreground">
                {t('table.no-result')}
            </div>
        );
    }
    
    if (!CardComponent) {
        return (
            <div className="flex items-center justify-center h-24 text-center text-muted-foreground">
                {t('table.no-result')}
            </div>
        );
    }
    
    const { table } = context;
    const rowModel = table?.getRowModel();
    const rows = rowModel?.rows;

    return (
        <div 
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4 min-w-0 w-full h-full"
            role="list"
            aria-label={t('table.entities_list', 'Entities list')}
            data-testid="list-entities"
        >
            {rows?.length ? (
                rows.map(row => (
                    <div
                        key={row.id}
                        role="listitem"
                        tabIndex={0}
                        className="min-w-0 w-full h-full"
                        data-testid={`card-entity-${row.id}`}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                onRowClick?.(row.original);
                            }
                        }}
                    >
                        <CardComponent
                            entity={row.original}
                            actions={cardActions}
                            onRowClick={onRowClick}
                        />
                    </div>
                ))
            ) : (
                <div className="col-span-full flex items-center justify-center h-24 text-center text-muted-foreground">
                    {t('table.no-result')}
                </div>
            )}
        </div>
    );
};

const CardLoading = () => (
    <div 
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4 min-w-0 w-full h-full"
        role="list"
        aria-label="Loading entities"
        data-testid="list-entities"
    >
        {Array.from({ length: 5 }).map((_, index) => (
            <div key={`skeleton-card-${index}`} className="p-4 border rounded-lg min-w-0 w-full h-full" role="listitem">
                <Skeleton className="w-full h-20 mb-2" />
                <Skeleton className="w-3/4 h-4 mb-1" />
                <Skeleton className="w-1/2 h-4" />
            </div>
        ))}
    </div>
);

const CardError = () => {
    const context = useEntityTableContext();
    const { t } = useTranslation();
    
    if (!context) return null;
    
    const { error, refetch } = context;
    
    return (
        <div className="flex flex-col items-center justify-center p-6 text-center">
            <Icon name="AlertCircle" className="h-8 w-8 text-destructive mb-3" data-testid="icon-error" />
            <p className="text-slate-400 mb-4" data-testid="text-error">
                {error?.message || t('error.loading_data_failed')}
            </p>
            {refetch && (
                <Button 
                    onClick={() => refetch()} 
                    variant="outline" 
                    size="sm"
                    className="flex items-center gap-2"
                    data-testid="button-retry"
                >
                    <Icon name="RefreshCw" className="h-4 w-4" />
                    {t('error.try_again')}
                </Button>
            )}
        </div>
    );
};

const Loading = () => (
    <>
        {Array.from({ length: 5 }).map((_, rowIndex) => (
            <TableRow key={`skeleton-row-${rowIndex}`} className="w-full">
                <TableCell className="h-12">
                    <Skeleton className="w-full h-full" />
                </TableCell>
                <TableCell className="h-12">
                    <Skeleton className="w-full h-full" />
                </TableCell>
                <TableCell className="h-12">
                    <Skeleton className="w-full h-full" />
                </TableCell>
                <TableCell className="h-12">
                    <Skeleton className="w-full h-full" />
                </TableCell>
                <TableCell className="h-12">
                    <Skeleton className="w-full h-full" />
                </TableCell>
            </TableRow>
        ))}
    </>
);

interface ErrorDisplayProps {
    columns: number;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ columns }) => {
    const context = useEntityTableContext();
    const { t } = useTranslation();
    
    if (!context) return null;
    
    const { error, refetch } = context;
    
    return (
        <TableRow>
            <TableCell colSpan={columns} className="h-32">
                <div className="flex flex-col items-center justify-center p-6 text-center">
                    <Icon name="AlertCircle" className="h-8 w-8 text-destructive mb-3" data-testid="icon-error" />
                    <p className="text-slate-400 mb-4" data-testid="text-error">
                        {error?.message || t('error.loading_data_failed')}
                    </p>
                    {refetch && (
                        <Button 
                            onClick={() => refetch()} 
                            variant="outline" 
                            size="sm"
                            className="flex items-center gap-2"
                            data-testid="button-retry"
                        >
                            <Icon name="RefreshCw" className="h-4 w-4" />
                            {t('error.try_again')}
                        </Button>
                    )}
                </div>
            </TableCell>
        </TableRow>
    );
};

export function EntityDataTable<TData, TValue>({
    columns,
    onRowClick,
    CardComponent,
    cardActions
}: Readonly<DataTableProps<TData, TValue>>) {
    const context = useEntityTableContext();
    
    if (!context) return null;
    
    const { isLoading, isError } = context;

    return (
        <div className="w-full">
            {/* Always show cards when CardComponent is available */}
            {CardComponent ? (
                <div>
                    {isLoading ? (
                        <CardLoading />
                    ) : isError ? (
                        <CardError />
                    ) : (
                        <Cards 
                            onRowClick={onRowClick} 
                            CardComponent={CardComponent}
                            cardActions={cardActions}
                            columns={columns}
                        />
                    )}
                </div>
            ) : (
                // Fallback to table view only when no CardComponent is available
                <div>
                    <ScrollableTable minWidth="640px">
                        <Table className="w-full min-w-0">
                            <TableHeader><Headers /></TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <Loading />
                                ) : isError ? (
                                    <ErrorDisplay columns={columns.length} />
                                ) : (
                                    <Rows onRowClick={onRowClick} columns={columns} />
                                )}
                            </TableBody>
                        </Table>
                    </ScrollableTable>
                </div>
            )}
        </div>
    );
}
