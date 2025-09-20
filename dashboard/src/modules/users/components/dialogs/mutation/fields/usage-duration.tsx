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

export const UsageDurationField: React.FC = () => {
    const form = useFormContext();
    const { t } = useTranslation();

    const defaultDuration = (form.getValues('usage_duration') ?? 0) / 86400;
    const [duration, setDuration] = React.useState<number>(defaultDuration);

    React.useEffect(() => {
        form.setValue('usage_duration', duration * 86400);
    }, [form, duration]);

    return (
        <FormField
            control={form.control}
            name="usage_duration"
            render={({ field }) => (
                <FormItem>
                    <FormLabel>{t('page.users.usage_duration')} ({t('days')})</FormLabel>
                    <FormControl>
                        <Input
                            {...field}
                            type="number"
                            value={duration}
                            onChange={(e) => {
                                setDuration(Number(e.target.value));
                                field.onChange(e.target.value);
                            }}
                        />
                    </FormControl>
                    <FormMessage />
                </FormItem>
            )}
        />
    );
}
