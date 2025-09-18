import {
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    Select,
    SelectTrigger,
    SelectContent,
    SelectItem,
    SelectValue,
} from '@wildosvpn/common/components';
import * as React from 'react'
import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

interface DataLimitResetStrategyFieldProps { }

export const DataLimitResetStrategyField: React.FC<DataLimitResetStrategyFieldProps> = () => {
    const { t } = useTranslation()
    const form = useFormContext()
    return (
        <FormField
            control={form.control}
            name="data_limit_reset_strategy"
            render={({ field }) => (
                <FormItem className="w-full">
                    <FormLabel>{t('page.users.data_limit_reset_strategy')}</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                            <SelectTrigger>
                                <SelectValue placeholder={t("placeholders.select-date")} />
                            </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                            <SelectItem value="no_reset">{t('options.none')}</SelectItem>
                            <SelectItem value="day">{t('time-periods.daily')}</SelectItem>
                            <SelectItem value="week">{t('time-periods.weekly')}</SelectItem>
                            <SelectItem value="month">{t('time-periods.monthly')}</SelectItem>
                            <SelectItem value="year">{t('time-periods.yearly')}</SelectItem>
                        </SelectContent>
                    </Select>
                    <FormMessage />
                </FormItem>
            )}
        />
    );
}
