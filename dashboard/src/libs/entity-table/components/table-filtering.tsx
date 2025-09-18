import * as React from "react";
import { Input } from "@wildosvpn/common/components";
import {
    useEntityTableContext
} from "@wildosvpn/libs/entity-table/contexts";
import { useTranslation } from "react-i18next";
import { useDebouncedCallback } from 'use-debounce';

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
        <Input
            placeholder={t('table.filter-placeholder', { name: primaryFilter.column })}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className=" w-full md:w-[20rem]"
        />
    );
}
