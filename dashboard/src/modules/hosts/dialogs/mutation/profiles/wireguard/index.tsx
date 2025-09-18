import {
    AllowedIpsField,
    CommonFields,
    DNSServersField,
    MtuField,
} from "../../fields";
import {
    Accordion,
    ClearableTextField,
} from "@wildosvpn/common/components";
import { SettingSection } from "@wildosvpn/modules/hosts";
import { useTranslation } from "react-i18next";

export const WireguardProfileFields = () => {
    const { t } = useTranslation();
    return (
        <div className="space-y-4 sm:space-y-6">
            <CommonFields />
            <Accordion className="space-y-4 sm:space-y-2" type="single" collapsible>
                <SettingSection value="wireguard" triggerText={t("wireguard")}>
                    {/* Vertical stacking on mobile */}
                    <div className="flex flex-col sm:flex-row gap-4 sm:gap-2">
                        <ClearableTextField
                            name="path"
                            label={t("page.hosts.server-public-key")}
                        />
                        <MtuField />
                    </div>
                    <div className="space-y-4 sm:space-y-6">
                        <DNSServersField />
                        <AllowedIpsField />
                    </div>
                </SettingSection>
            </Accordion>
        </div>
    );
};

export * from "./schema";
export * from "./default";
