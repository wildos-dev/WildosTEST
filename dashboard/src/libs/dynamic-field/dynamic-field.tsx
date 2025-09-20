import * as React from 'react';
import { useFormContext, Controller } from "react-hook-form";
import { Input, Button, Separator } from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { useTranslation } from "react-i18next";

interface DynamicFieldProps {
    fieldIndex: number;
    parentFieldName: string;
    onRemove: () => void;
}

export const DynamicField: React.FC<DynamicFieldProps> = ({
    fieldIndex,
    parentFieldName,
    onRemove,
}) => {
    const formContext = useFormContext();
    const { t } = useTranslation();

    if (!formContext) {
        return null;
    }

    const { control } = formContext;

    return (
        <div className="hstack gap-2 mt-1">
            <div className="hstack gap-0 items-center border-ghost border-2 rounded-md">
                <Controller
                    name={`${parentFieldName}.${fieldIndex}.name`}
                    control={control}
                    render={({ field }) => (
                        <Input
                            {...field}
                            className="border-none bg-transparent w-2/5 focus-visible:ring-offset-0 focus-visible:ring-0 text-end"
                            placeholder={t("placeholders.header-name")}
                        />
                    )}
                />
                <Separator className="h-2/4" orientation="vertical" />
                <Controller
                    name={`${parentFieldName}.${fieldIndex}.value`}
                    control={control}
                    render={({ field }) => (
                        <Input
                            {...field}
                            className="border-none bg-transparent w-3/5 focus-visible:ring-0 focus-visible:ring-offset-0 text-start"
                            placeholder={t("placeholders.header-value")}
                        />
                    )}
                />
            </div>
            <Button
                variant="secondary-destructive"
                size="icon"
                onClick={onRemove}
            >
                <Icon name="ListX" />
            </Button>
        </div>
    );
};
