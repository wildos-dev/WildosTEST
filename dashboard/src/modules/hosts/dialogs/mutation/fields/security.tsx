import {
    ClearableTextField,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@wildosvpn/common/components";
import * as React from 'react';
import { useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { AllowInsecureField, AlpnField, FingerprintField } from ".";

export const SecurityFields = () => {
    const { t } = useTranslation();
    const form = useFormContext();
    const security = form.watch().security;

    const [extraSecurity, setExtraSecurity] = React.useState<boolean>(
        ["tls", "inbound_default"].includes(security),
    );
    React.useEffect(() => {
        setExtraSecurity(["tls", "inbound_default"].includes(security));
    }, [security, setExtraSecurity]);

    return (
        <>
            <FormField
                control={form.control}
                name="security"
                render={({ field }) => (
                    <FormItem>
                        <FormLabel>{t("security")}</FormLabel>
                        <Select
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                        >
                            <FormControl>
                                <SelectTrigger>
                                    <SelectValue placeholder={t("placeholders.select-security")} />
                                </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                                <SelectItem value="none">{t("options.none")}</SelectItem>
                                <SelectItem value="tls">{t("options.tls")}</SelectItem>
                                <SelectItem value="inbound_default">
                                    {t("options.inbound-default")}
                                </SelectItem>
                            </SelectContent>
                        </Select>
                        <FormMessage />
                    </FormItem>
                )}
            />
            {extraSecurity && (
                <div className="w-full flex flex-col gap-2">
                    <ClearableTextField name="sni" label={t("sni")} />
                    <div className="flex flex-row w-full gap-2">
                        <AlpnField />
                        <FingerprintField />
                    </div>
                    <AllowInsecureField />
                </div>
            )}
        </>
    );
};
