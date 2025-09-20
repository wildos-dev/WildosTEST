import {
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    Input,
    Button,
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@wildosvpn/common/components";
import type { FieldErrors, FieldError } from "react-hook-form";
import { useWatch, useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import * as React from "react";

interface FragmentForm {
    fragment: {
        packets: FieldError;
        length: FieldError;
        interval: FieldError;
    };
}

const FragmentErrorPopover: React.FC = () => {
    const form = useFormContext();
    const { t } = useTranslation();
    const errors = form.formState.errors as FieldErrors<FragmentForm>;
    return (
        <Popover>
            <PopoverTrigger>
                <Icon name="MailWarning" className="p-0 size-5 text-destructive bg-primary-background" />
            </PopoverTrigger>
            <PopoverContent className="bg-destructive-accent text-sm">
                <ul className="my-6 ml-3 list-disc [&>li]:mt-1 mt-0">
                    {errors.fragment?.length?.message && (
                        <li>
                            <b>Length:</b> {t(String(errors.fragment.length.message || ''))}
                        </li>
                    )}
                    {errors.fragment?.packets?.message && (
                        <li>
                            <b>Packets:</b> {t(String(errors.fragment.packets.message || ''))}
                        </li>
                    )}
                    {errors.fragment?.interval?.message && (
                        <li>
                            <b>Interval:</b> {t(String(errors.fragment.interval.message || ''))}
                        </li>
                    )}
                </ul>
            </PopoverContent>
        </Popover>
    );
};

export const FragmentField = () => {
    const { t } = useTranslation();
    const form = useFormContext();
    const errors = form.formState.errors as FieldErrors<FragmentForm>;
    const fragment = useWatch({ name: "fragment" });
    const disabled = fragment === null || fragment === undefined;

    const enable = () => {
        form.setValue(
            "fragment",
            { length: "", packets: "", interval: "" },
            {
                shouldTouch: true,
                shouldDirty: true,
            },
        );
    };

    const disable = () => {
        form.setValue("fragment.length", "");
        form.setValue("fragment.packets", "");
        form.setValue("fragment.interval", "");
        form.setValue("fragment", null, {
            shouldValidate: true,
            shouldTouch: false,
            shouldDirty: false,
        });
    };

    const hasFragmentErrors = (errors: FieldErrors<FragmentForm>) =>
        errors.fragment?.packets ||
        errors.fragment?.length ||
        errors.fragment?.interval;

    return (
        <FormField
            control={form.control}
            name="fragment"
            render={() => (
                <FormItem className="my-2 w-full">
                    <FormLabel className="flex flex-row justify-between items-center">
                        {t("fragment")}
                        <div className="flex flex-row items-center gap-2">
                            {hasFragmentErrors(errors) && <FragmentErrorPopover />}
                            {!disabled && (
                                <Button
                                    variant="destructive"
                                    className="p-0 size-5 bg-primary-background"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        disable();
                                    }}
                                >
                                    <Icon name="Trash" className="text-red-400" />
                                </Button>
                            )}
                        </div>
                    </FormLabel>

                    <FormControl>
                        <div className="flex flex-row w-full items-center">
                            {!disabled ? (
                                <>
                                    <FormField
                                        name="fragment.packets"
                                        render={({ field }) => (
                                            <div className="flex flex-col">
                                                <FormItem>
                                                    <FormLabel className="font-medium">
                                                        {t("page.hosts.fragment.packets")}
                                                    </FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            className="border rounded-none rounded-s-lg p-2 w-full"
                                                            {...field}
                                                        />
                                                    </FormControl>
                                                </FormItem>
                                            </div>
                                        )}
                                    />
                                    <FormField
                                        name="fragment.length"
                                        render={({ field }) => (
                                            <div className="flex flex-col">
                                                <FormItem>
                                                    <FormLabel className="font-medium">
                                                        {t("page.hosts.fragment.length")}
                                                    </FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            className="rounded-none w-full p-2"
                                                            {...field}
                                                        />
                                                    </FormControl>
                                                </FormItem>
                                            </div>
                                        )}
                                    />
                                    <FormField
                                        name="fragment.interval"
                                        render={({ field }) => (
                                            <div className="flex flex-col">
                                                <FormItem>
                                                    <FormLabel className="font-medium">
                                                        {t("page.hosts.fragment.interval")}
                                                    </FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            className="border w-full rounded-none rounded-e-lg p-2"
                                                            {...field}
                                                        />
                                                    </FormControl>
                                                </FormItem>
                                            </div>
                                        )}
                                    />
                                </>
                            ) : (
                                <Button
                                    className="border w-full"
                                    variant="ghost"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        enable();
                                    }}
                                >
                                    {t("disabled")}
                                </Button>
                            )}
                        </div>
                    </FormControl>
                </FormItem>
            )}
        />
    );
};
