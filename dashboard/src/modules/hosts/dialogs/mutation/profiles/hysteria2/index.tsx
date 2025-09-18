import { CommonFields } from "../../fields";
import { TlsFields } from "../../sections";
import { Accordion, ClearableTextField } from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";

export const Hysteria2ProfileFields = () => {
    const { t } = useTranslation();
    return (
        <div className="space-y-4 sm:space-y-6">
            <CommonFields />
            <div className="space-y-4">
                <ClearableTextField
                    name="path"
                    label={t("page.hosts.obfuscation-password")}
                />
            </div>
            <Accordion className="space-y-4 sm:space-y-2" type="single" collapsible>
                <TlsFields />
            </Accordion>
        </div>
    );
};

export * from "./schema";
export * from "./default";
