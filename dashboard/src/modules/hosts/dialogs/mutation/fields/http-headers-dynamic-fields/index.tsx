import {
    AlertCard,
    Button,
    Label,
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
        <div className="mt-2 flex flex-col gap-4 sm:gap-2">
            <Label className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-0 font-semibold">
                <span className="text-sm sm:text-base">{t("page.hosts.http_headers")}</span>
                <div className="flex flex-row gap-2 sm:gap-1 items-center w-full sm:w-auto justify-end">
                    <Button
                        variant="secondary"
                        size="touch-sm"
                        disabled={previousValues.length === 0}
                        className="h-10 w-10 sm:h-8 sm:w-8 p-0 focus-visible:opacity-100"
                        onClick={handleRestorePrevious}
                        title={t("common.restore_previous_values") || "Restore previous values"}
                    >
                        <Icon name="RotateCcw" className="h-4 w-4 sm:h-5 sm:w-5" />
                    </Button>
                    <Button
                        variant="secondary-destructive"
                        size="touch-sm"
                        disabled={!fields.length}
                        className="h-10 w-10 sm:h-8 sm:w-8 p-0 focus-visible:opacity-100"
                        onClick={handleReplaceAll}
                    >
                        <Icon name="Trash" className="h-4 w-4 sm:h-5 sm:w-5" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="touch-sm"
                        className="h-10 w-10 sm:h-8 sm:w-8 p-0 focus-visible:opacity-100"
                        onClick={handleAppend}
                    >
                        <Icon name="ListPlus" className="h-4 w-4 sm:h-5 sm:w-5" />
                    </Button>
                </div>
            </Label>
            
            {/* Mobile-first layout for headers */}
            <div className="flex flex-col space-y-4">
                {fields.length !== 0 ? (
                    <div className="space-y-3 sm:space-y-2">
                        {fields.map((field, index) => {
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
                                    {/* Each header as separate card/item on mobile */}
                                    <div className="p-4 sm:p-3 border rounded-lg bg-card">
                                        <DynamicField
                                            fieldIndex={index}
                                            parentFieldName="http_headers"
                                            onRemove={() => handleRemove(index, field.id)}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <AlertCard
                        size="wide-full"
                        title={t("page.hosts.no-http-headers")}
                    />
                )}
            </div>
        </div>
    );
};
