import {
        FormControl,
        FormField,
        FormItem,
        FormLabel,
        Checkbox,
} from "@wildosvpn/common/components";
import { useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";

export const MuxField = () => {
        const { t } = useTranslation();
        const form = useFormContext();
        return (
                <FormField
                        control={form.control}
                        name="mux"
                        render={({ field }) => (
                                <FormItem>
                                        <FormLabel>{t("mux")}</FormLabel>
                                        <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4 shadow">
                                                <FormControl>
                                                        <Checkbox
                                                                checked={field.value}
                                                                onCheckedChange={field.onChange}
                                                        />
                                                </FormControl>
                                                <div className="space-y-1 leading-none">
                                                        <label className="font-semibold text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">{t("page.hosts.mux.title")}</label>
                                                        <p className="text-sm text-muted-foreground">{t("page.hosts.mux.desc")}</p>
                                                </div>
                                        </div>
                                </FormItem>
                        )}
                />
        );
};
