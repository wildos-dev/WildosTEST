import { Card, CardContent } from "@wildosvpn/common/components";
import { cn } from "@wildosvpn/common/utils";
import { CardRowProps } from '../types';
import { ColumnDef } from "@tanstack/react-table";

export function CardRowRenderer<TData>({ 
  row, 
  columns, 
  onRowClick, 
  className 
}: CardRowProps<TData>) {
  const handleClick = () => {
    if (onRowClick) {
      onRowClick(row);
    }
  };

  const renderCellValue = (column: ColumnDef<TData, unknown>, row: TData) => {
    if (column.cell && typeof column.cell === 'function') {
      return column.cell({ 
        row: { original: row }, 
        column: column as any,
        cell: {} as any,
        getValue: () => '',
        renderValue: () => '',
        table: {} as any
      });
    }
    
    if (column.accessorKey) {
      return (row as any)[column.accessorKey];
    }
    
    if (column.accessorFn && typeof column.accessorFn === 'function') {
      return column.accessorFn(row);
    }
    
    return '';
  };

  const getColumnHeader = (column: ColumnDef<TData, unknown>) => {
    if (typeof column.header === 'string') {
      return column.header;
    }
    if (typeof column.header === 'function') {
      return column.header({} as any);
    }
    return column.id || (column.accessorKey as string) || '';
  };

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-md transition-shadow duration-200 mb-2",
        className
      )}
      onClick={handleClick}
      data-testid={`card-row-${(row as any).id || 'unknown'}`}
    >
      <CardContent className="p-4 space-y-2">
        {columns.map((column: ColumnDef<TData, unknown>, index) => {
          const header = getColumnHeader(column);
          const value = renderCellValue(column, row);
          
          if (!value && value !== 0) return null;
          
          return (
            <div key={column.id || column.accessorKey || index} className="flex justify-between items-start">
              <span className="text-sm font-medium text-muted-foreground min-w-0 flex-shrink-0 mr-2">
                {header}:
              </span>
              <span className="text-sm text-foreground text-right min-w-0 flex-1 break-words">
                {value}
              </span>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}