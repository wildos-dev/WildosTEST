import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";

export const SplitHttpModeField = (
    { updater }: { updater: (field: string, value: any) => void }
) => {
    const { t } = useTranslation();
    return (
        <FormField
            name="splithttp_settings.mode"
            render={({ field }) => (
                <FormItem>
                    <FormLabel >
                        {t("Mode")}
                    </FormLabel>
                    <Select onValueChange={(value) => updater("splithttp_settings.mode", value)} defaultValue={field.value}>
                        <FormControl>
                            <SelectTrigger>
                                <SelectValue placeholder={t("placeholders.select-mode")} />
                            </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                            <SelectItem value="auto">auto</SelectItem>
                            <SelectItem value="packet-up">packet-up</SelectItem>
                            <SelectItem value="stream-up">stream-up</SelectItem>
                            <SelectItem value="stream-one">stream-one</SelectItem>
                        </SelectContent>
                    </Select>
                </FormItem>
            )}
        />
    )
}
