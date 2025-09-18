import * as React from "react";
import {
    FormControl,
    FormField,
    FormItem,
    Input,
    FormLabel,
    FormMessage,
} from "@wildosvpn/common/components";
import { useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";

export const SubscriptionUrlPrefixField: React.FC<React.InputHTMLAttributes<HTMLElement>> = ({
    disabled,
}) => {
    const form = useFormContext();
    const { t } = useTranslation();

    return (
        <FormField
            control={form.control}
            name="subscription_url_prefix"
            render={({ field }) => (
                <FormItem>
                    <FormLabel>{t("page.admins.subscription-url-prefix")}</FormLabel>
                    <FormControl>
                        <Input disabled={disabled} {...field} />
                    </FormControl>
                    <FormMessage />
                </FormItem>
            )}
        />
    );
};
