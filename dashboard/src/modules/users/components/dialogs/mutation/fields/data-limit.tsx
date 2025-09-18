import {
    FormControl,
    FormField,
    FormItem,
    Input,
    FormLabel,
    FormMessage
} from '@wildosvpn/common/components';
import * as React from 'react'
import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

interface DataLimitFieldProps { }

export const DataLimitField: React.FC<DataLimitFieldProps> = () => {
    const { t } = useTranslation()
    const form = useFormContext()
    return (
        <FormField
            control={form.control}
            name="data_limit"
            render={({ field }) => (
                <FormItem className="w-full">
                    <FormLabel>{t('page.users.traffic')}</FormLabel>
                    <FormControl>
                        <Input
                            type="number"
                            className="order-1"
                            {...field}
                            placeholder={t("placeholders.gb")}
                        />
                    </FormControl>
                    <FormMessage />
                </FormItem>
            )}
        />
    );
}
