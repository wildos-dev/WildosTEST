import {
    AlertCard,
    Button,
    FormLabel,
    ScrollArea,
} from "@wildosvpn/common/components";
import { useFieldArray, useFormContext } from "react-hook-form";
import { DynamicField } from "@wildosvpn/libs/dynamic-field";
import { useTranslation } from "react-i18next";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { useState, useRef, useCallback } from "react";

export const HttpHeadersDynamicFields = () => {
    const { t } = useTranslation();
    const { control } = useFormContext();

    const { fields, append, remove, replace } = useFieldArray({
        control,
        name: "http_headers",
    });

    // State for storing previous values for restore functionality
    const [previousValues, setPreviousValues] = useState<any[]>([]);
    const [removingItems, setRemovingItems] = useState<Set<string>>(new Set());
    const timeoutRefs = useRef<Map<string, NodeJS.Timeout>>(new Map());

    // Store current values as previous before making changes
    const storePreviousValues = useCallback(() => {
        setPreviousValues([...fields]);
    }, [fields]);

    // Enhanced append with animation and state storage
    const handleAppend = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        storePreviousValues();
        append({ name: "", value: "" });
    }, [append, storePreviousValues]);

    // Enhanced remove with animation
    const handleRemove = useCallback((index: number, fieldId: string) => {
        storePreviousValues();
        setRemovingItems(prev => new Set(prev).add(fieldId));
        
        const timeout = setTimeout(() => {
            remove(index);
            setRemovingItems(prev => {
                const newSet = new Set(prev);
                newSet.delete(fieldId);
                return newSet;
            });
            timeoutRefs.current.delete(fieldId);
        }, 200); // Animation duration
        
        timeoutRefs.current.set(fieldId, timeout);
    }, [remove, storePreviousValues]);

    // Enhanced replace all with state storage
    const handleReplaceAll = useCallback(() => {
        storePreviousValues();
        replace([]);
    }, [replace, storePreviousValues]);

    // Restore to previous values
    const handleRestorePrevious = useCallback(() => {
        if (previousValues.length > 0) {
            replace(previousValues);
        }
    }, [previousValues, replace]);

    return (
        <div className="mt-2 flex flex-col gap-2">
            <FormLabel className="hstack justify-between items-center">
                {t("page.hosts.http_headers")}
                <div className="hstack gap-1 items-center [*>button]:p-1">
                    <Button
                        variant="secondary"
                        size="icon"
                        disabled={previousValues.length === 0}
                        className="p-1"
                        onClick={handleRestorePrevious}
                        title={t("common.restore_previous_values") || "Restore previous values"}
                    >
                        <Icon name="RotateCcw" className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="secondary-destructive"
                        size="icon"
                        disabled={!fields.length}
                        className="p-1"
                        onClick={handleReplaceAll}
                    >
                        <Icon name="Trash" className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="p-1"
                        onClick={handleAppend}
                    >
                        <Icon name="ListPlus" className="h-4 w-4" />
                    </Button>
                </div>
            </FormLabel>
            <ScrollArea className="p-2 border-2  h-[7rem] max-h-[10rem]  bg-background grid grid-cols-1 gap-2 rounded-md">
                {fields.length !== 0 ? (
                    fields.map((field, index) => {
                        const isRemoving = removingItems.has(field.id);
                        return (
                            <div
                                key={field.id}
                                className={`transition-all duration-200 ease-in-out transform ${
                                    isRemoving 
                                        ? 'opacity-0 scale-95 -translate-y-2' 
                                        : 'opacity-100 scale-100 translate-y-0 animate-in slide-in-from-bottom-2 duration-300'
                                }`}
                            >
                                <DynamicField
                                    fieldIndex={index}
                                    parentFieldName="http_headers"
                                    onRemove={() => handleRemove(index, field.id)}
                                />
                            </div>
                        );
                    })
                ) : (
                    <AlertCard
                        size="wide-full"
                        title={t("page.hosts.no-http-headers")}
                    ></AlertCard>
                )}
            </ScrollArea>
        </div>
    );
};
