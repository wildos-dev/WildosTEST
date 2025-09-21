import * as React from "react";
import { format } from "date-fns";
import { CalendarIcon } from "@radix-ui/react-icons";
import { cn } from "@wildosvpn/common/utils";
import { useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";
import {
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    FormDescription,
    Input,
    Checkbox,
    Button,
    Popover,
    PopoverTrigger,
    PopoverContent,
    Calendar,
    Icon,
} from "@wildosvpn/common/components";

// Base field props interface
interface BaseFieldProps {
    name: string;
    label: string;
    description?: string;
    className?: string;
    disabled?: boolean;
}

// Text Field Component
interface TextFieldProps extends BaseFieldProps {
    placeholder?: string;
    type?: "text" | "email" | "password" | "number";
}

export const TextField: React.FC<TextFieldProps> = ({
    name,
    label,
    placeholder = "",
    type = "text",
    description,
    className,
    disabled = false,
}) => {
    const form = useFormContext();
    const { t } = useTranslation();

    return (
        <FormField
            control={form.control}
            name={name}
            render={({ field }) => (
                <FormItem className={cn("w-full", className)}>
                    <FormLabel>{t(label)}</FormLabel>
                    <FormControl>
                        <Input
                            type={type}
                            placeholder={t(placeholder)}
                            disabled={disabled}
                            {...field}
                        />
                    </FormControl>
                    {description && (
                        <FormDescription>{t(description)}</FormDescription>
                    )}
                    <FormMessage />
                </FormItem>
            )}
        />
    );
};

// Checkbox Field Component  
interface CheckboxFieldProps extends BaseFieldProps {
}

export const CheckboxField: React.FC<CheckboxFieldProps> = ({
    name,
    label,
    description,
    className,
    disabled = false,
}) => {
    const form = useFormContext();
    const { t } = useTranslation();

    return (
        <FormField
            control={form.control}
            name={name}
            render={({ field }) => (
                <FormItem className={cn(
                    "flex flex-row items-start space-x-3 space-y-0 rounded-md py-2",
                    className
                )}>
                    <FormControl>
                        <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                            disabled={disabled}
                            aria-describedby={description ? `${name}-description` : undefined}
                        />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                        <FormLabel>{t(label)}</FormLabel>
                        {description && (
                            <FormDescription id={`${name}-description`}>
                                {t(description)}
                            </FormDescription>
                        )}
                    </div>
                    <FormMessage />
                </FormItem>
            )}
        />
    );
};

// Clearable Text Field Component
interface ClearableTextFieldProps extends BaseFieldProps {
    placeholder?: string;
}

export const ClearableTextField: React.FC<ClearableTextFieldProps> = ({
    name,
    label,
    placeholder = "",
    description,
    className,
    disabled = false,
}) => {
    const { t } = useTranslation();
    const form = useFormContext();
    const value = form.watch(name);

    const handleClear = () => {
        form.setValue(name, null);
    };

    const handleRestore = () => {
        form.setValue(name, "");
    };

    return (
        <FormField
            control={form.control}
            name={name}
            render={({ field }) => (
                <FormItem className={cn("w-full", className)}>
                    <FormLabel>{t(label)}</FormLabel>
                    <FormControl>
                        <div className="relative w-full flex items-center gap-2">
                            {value === null ? (
                                <div className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium">
                                    null
                                </div>
                            ) : (
                                <Input 
                                    placeholder={t(placeholder)} 
                                    disabled={disabled}
                                    {...field} 
                                />
                            )}
                            <Button
                                type="button"
                                aria-label={t('accessibility.clear-field', { field: t(label) })}
                                variant="ghost"
                                size="icon"
                                onClick={value === null ? handleRestore : handleClear}
                                disabled={disabled}
                                className="absolute hover:fg-destructive-background right-1 top-1/2 -translate-y-1/2 h-7"
                            >
                                <Icon name="X" className="h-4 w-4" />
                                <span className="sr-only">
                                    {t('accessibility.clear-field', { field: t(label) })}
                                </span>
                            </Button>
                        </div>
                    </FormControl>
                    {description && (
                        <FormDescription>{t(description)}</FormDescription>
                    )}
                    <FormMessage />
                </FormItem>
            )}
        />
    );
};

// Date Field Component
interface DateFieldProps extends BaseFieldProps {
}

function parseISODate(isoDateString: string | undefined): Date | undefined {
    if (!isoDateString) return undefined;
    const date = new Date(isoDateString);
    return isNaN(date.getTime()) ? undefined : date;
}

export const DateField: React.FC<DateFieldProps> = ({
    name,
    label,
    description,
    className,
    disabled = false,
}) => {
    const { t } = useTranslation();
    const form = useFormContext();
    const [selectedDate, setSelectedDate] = React.useState<Date | undefined>(
        parseISODate(form.getValues(name)),
    );

    React.useEffect(() => {
        const newValue = selectedDate?.toISOString().slice(0, -5);
        const prevValue = form.getValues(name);
        if (newValue !== prevValue) {
            form.setValue(name, newValue, {
                shouldValidate: true,
                shouldTouch: true,
                shouldDirty: true,
            });
        }
    }, [form, name, selectedDate]);

    return (
        <FormField
            control={form.control}
            name={name}
            render={({ field }) => (
                <FormItem className={cn("flex flex-col mt-2 w-full", className)}>
                    <FormLabel>{t(label)}</FormLabel>
                    <Popover>
                        <PopoverTrigger asChild>
                            <FormControl>
                                <Button
                                    variant="outline"
                                    disabled={disabled}
                                    aria-label={t('accessibility.select-date', { field: t(label) })}
                                    className={cn(
                                        "w-full pl-3 text-left font-normal",
                                        !field.value && "text-muted-foreground",
                                    )}
                                >
                                    {field.value ? (
                                        format(field.value + "Z", "PPP")
                                    ) : (
                                        <span>{t('form.pick-a-date')}</span>
                                    )}
                                    <CalendarIcon className="ml-auto w-4 h-4 opacity-50" />
                                </Button>
                            </FormControl>
                        </PopoverTrigger>
                        <PopoverContent className="p-0 w-auto" align="start">
                            <Calendar
                                mode="single"
                                {...field}
                                selected={selectedDate}
                                onSelect={(date) => {
                                    setSelectedDate(date);
                                }}
                                disabled={(date) => date < new Date() || disabled}
                                initialFocus
                            />
                        </PopoverContent>
                    </Popover>
                    {description && (
                        <FormDescription>{t(description)}</FormDescription>
                    )}
                    <FormMessage />
                </FormItem>
            )}
        />
    );
};

// Export all field components
export const UnifiedFormFields = {
    TextField,
    CheckboxField,
    ClearableTextField,
    DateField,
};