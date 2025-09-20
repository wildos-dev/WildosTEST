import {
    OpenInNewWindowIcon,
} from "@radix-ui/react-icons"
import { Row } from "@tanstack/react-table"

import {
    Button,
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from "@wildosvpn/common/components"
import { Icon } from "@wildosvpn/common/components/ui/icon"
import { useTranslation } from "react-i18next"

interface DataTableActionsCellProps<TData>
    extends React.HTMLAttributes<HTMLDivElement> {
    row: Row<TData>,
    onDelete: (object: TData) => void,
    onEdit: (object: TData) => void,
    onOpen: (object: TData) => void,
}

export function DataTableActionsCell<TData>({
    row, onDelete, onEdit, onOpen
}: DataTableActionsCellProps<TData>) {
    const { t } = useTranslation();

    return (
        <div className="flex gap-1 sm:gap-2 opacity-100 sm:opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
            {/* Edit Button */}
            <Button
                variant="secondary"
                size="touch-sm"
                onClick={(e) => {
                    e.stopPropagation();
                    onEdit(row.original);
                }}
                className="focus-visible:opacity-100 shadow-sm"
                title={t('edit')}
                data-testid="action-row-edit"
            >
                <Icon name="Edit" className="h-4 w-4 sm:h-5 sm:w-5" />
            </Button>
            
            {/* Delete Button */}
            <Button
                variant="destructive"
                size="touch-sm"
                onClick={(e) => {
                    e.stopPropagation();
                    onDelete(row.original);
                }}
                className="focus-visible:opacity-100 shadow-sm"
                title={t('delete')}
                data-testid="action-row-delete"
            >
                <Icon name="Trash2" className="h-4 w-4 sm:h-5 sm:w-5" />
            </Button>
            
            {/* More Actions Dropdown for additional actions */}
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button 
                        variant="ghost" 
                        size="touch-sm" 
                        data-testid="action-menu-open" 
                        className="focus-visible:opacity-100 shadow-sm"
                        title={t('navigation.open-menu')}
                    >
                        <span className="sr-only">{t('navigation.open-menu')}</span>
                        <Icon name="MoreHorizontal" className="h-4 w-4 sm:h-5 sm:w-5" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuLabel>{t('actions')}</DropdownMenuLabel>
                    <DropdownMenuItem data-testid="action-row-open" onClick={() => { onOpen(row.original) }}>
                        <OpenInNewWindowIcon className="mr-1 w-4 h-4" /> {t('open')}
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    )
}
