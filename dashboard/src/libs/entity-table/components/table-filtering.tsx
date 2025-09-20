import * as React from "react";
import { Input } from "@wildosvpn/common/components";
import {
    useEntityTableContext
} from "@wildosvpn/libs/entity-table/contexts";
import { useTranslation } from "react-i18next";
import { useDebouncedCallback } from 'use-debounce';
import { Icon } from "@wildosvpn/common/components/ui/icon";

interface TableSearchProps { }

export const TableSearch: React.FC<TableSearchProps> = () => {
    const { primaryFilter } = useEntityTableContext()
    const [keyword, setKeyword] = React.useState(primaryFilter.columnFilters)

    const setColumnFilters = useDebouncedCallback(
        primaryFilter.setColumnFilters,
        500
    );

    React.useEffect(() => {
        setColumnFilters(keyword);
    }, [keyword, setColumnFilters])

    const { t } = useTranslation()

    return (
        <div className="relative flex-1 max-w-full sm:max-w-md">
            <Icon name="Search" className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
                placeholder={t('table.filter-placeholder', { name: primaryFilter.column })}
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="pl-10"
            />
        </div>
    );
}
