import * as React from 'react';
import { cn } from "@wildosvpn/common/utils";
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@wildosvpn/common/components";
import { useTranslation } from 'react-i18next';

// Import existing entity-table components and hooks
import { 
  EntityTableContext,
  DataTablePagination,
  TableSearch,
  DataTableViewOptions,
} from '@wildosvpn/libs/entity-table';

import { useResponsiveColumns } from '../hooks/use-responsive-columns';
import { CardRowRenderer } from './card-row-renderer';
import { FilterDrawer } from './filter-drawer';
import { ResponsiveTableProps } from '../types';

export function ResponsiveEntityTable<TData>({
  columns,
  data,
  columnPresets,
  renderCard,
  enableCardView = true,
  cardViewBreakpoint = 'md',
  onRowClick,
  stickyHeader = true,
  className,
}: ResponsiveTableProps<TData>) {
  const { t } = useTranslation();
  const tableContext = React.useContext(EntityTableContext);
  
  // Use existing entity table data if available, otherwise fallback to props
  const tableData = tableContext?.table ? 
    tableContext.table.getRowModel().rows.map(row => row.original) : 
    data;
  const isLoading = tableContext?.isLoading || false;
  
  // Use context table columns if available, otherwise use responsive columns
  const contextColumns = tableContext?.table ? 
    tableContext.table.getVisibleLeafColumns().map(col => col.columnDef) : 
    columns;
  const { visibleColumns } = useResponsiveColumns(contextColumns, columnPresets);
  
  // Determine if we should show card view
  const showCardView = React.useMemo(() => {
    if (!enableCardView) return false;
    
    switch (cardViewBreakpoint) {
      case 'sm': return !useScreenBreakpoint('sm');
      case 'md': return !useScreenBreakpoint('md');
      case 'lg': return !useScreenBreakpoint('lg');
      default: return false;
    }
  }, [enableCardView, cardViewBreakpoint]);

  const [showFilters, setShowFilters] = React.useState(false);

  // Render card view for mobile
  if (showCardView) {
    return (
      <div className={cn("space-y-4", className)}>
        {/* Mobile toolbar */}
        <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center justify-between">
          <TableSearch />
          <div className="flex gap-2">
            <FilterDrawer 
              isOpen={showFilters}
              onOpenChange={setShowFilters}
            >
              <DataTableViewOptions table={tableContext?.table} />
            </FilterDrawer>
          </div>
        </div>

        {/* Card view */}
        <div className="space-y-2" data-testid="card-view-container">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : tableData.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {t('table.no-data', 'No data available')}
            </div>
          ) : (
            tableData.map((row, index) => (
              renderCard ? 
                renderCard({ row, columns: visibleColumns, onRowClick }) :
                <CardRowRenderer
                  key={index}
                  row={row}
                  columns={visibleColumns}
                  onRowClick={onRowClick}
                />
            ))
          )}
        </div>

        {/* Mobile pagination */}
        {tableContext?.table && (
          <DataTablePagination table={tableContext.table} />
        )}
      </div>
    );
  }

  // Desktop table view
  return (
    <div className={cn("space-y-4", className)}>
      {/* Desktop toolbar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <TableSearch />
        <div className="flex items-center gap-2">
          <DataTableViewOptions table={tableContext?.table} />
        </div>
      </div>

      {/* Table view */}
      <div className="rounded-md border">
        <div className="relative overflow-x-auto">
          <Table>
            <TableHeader className={cn(stickyHeader && "sticky top-0 bg-background z-10 border-b")}>
              <TableRow>
                {visibleColumns.map((column, index) => {
                  const header = (column as any).header;
                  return (
                    <TableHead 
                      key={(column as any).id || (column as any).accessorKey || index}
                      className="whitespace-nowrap"
                    >
                      {typeof header === 'function' ? header() : header}
                    </TableHead>
                  );
                })}
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell 
                    colSpan={visibleColumns.length} 
                    className="text-center py-8"
                  >
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </TableCell>
                </TableRow>
              ) : tableData.length === 0 ? (
                <TableRow>
                  <TableCell 
                    colSpan={visibleColumns.length} 
                    className="text-center py-8 text-muted-foreground"
                  >
                    {t('table.no-data', 'No data available')}
                  </TableCell>
                </TableRow>
              ) : (
                tableData.map((row, rowIndex) => (
                  <TableRow
                    key={rowIndex}
                    className={cn(
                      onRowClick && "cursor-pointer hover:bg-muted/50"
                    )}
                    onClick={() => onRowClick?.(row)}
                    data-testid={`table-row-${rowIndex}`}
                  >
                    {visibleColumns.map((column, colIndex) => {
                      const cell = (column as any).cell;
                      const accessorKey = (column as any).accessorKey;
                      const accessorFn = (column as any).accessorFn;
                      
                      let cellValue;
                      if (cell && typeof cell === 'function') {
                        cellValue = cell({ row: { original: row } });
                      } else if (accessorKey) {
                        cellValue = (row as any)[accessorKey];
                      } else if (accessorFn && typeof accessorFn === 'function') {
                        cellValue = accessorFn(row);
                      } else {
                        cellValue = '';
                      }

                      return (
                        <TableCell 
                          key={(column as any).id || (column as any).accessorKey || colIndex}
                          className="whitespace-nowrap"
                        >
                          {cellValue}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        
        {/* Desktop pagination */}
        {tableContext?.table && (
          <DataTablePagination table={tableContext.table} />
        )}
      </div>
    </div>
  );
}