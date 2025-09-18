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
    Button
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { useEntityTableContext } from "@wildosvpn/libs/entity-table/contexts";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import * as React from "react";

interface DataTableProps<TData, TValue> {
    columns: ColumnDef<TData, TValue>[]
    onRowClick?: (object: TData) => void
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
}: Readonly<DataTableProps<TData, TValue>>) {
    const context = useEntityTableContext();
    if (!context) return null;
    
    const { isLoading, isError } = context;

    return (
        <Table className="w-full">
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
    );
}
