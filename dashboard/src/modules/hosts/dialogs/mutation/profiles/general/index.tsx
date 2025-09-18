import {
    CommonFields,
    EarlyDataField,
    FragmentField,
    HttpHeadersDynamicFields,
    MuxSettingsFields,
    NoiseField,
    SecurityFields,
    SplitHttpFields,
} from "../../fields";
import {
    Accordion,
    ClearableTextField,
} from "@wildosvpn/common/components";
import { SettingSection } from "@wildosvpn/modules/hosts";
import { useTranslation } from "react-i18next";

export const GeneralProfileFields = () => {
    const { t } = useTranslation();

    return (
        <div className="space-y-4 sm:space-y-6">
            <CommonFields />
            <Accordion className="space-y-4 sm:space-y-2" type="single" collapsible>
                <SettingSection
                    value="network"
                    triggerText={t("page.hosts.network-settings")}
                >
                    {/* Vertical stacking on mobile */}
                    <div className="flex flex-col sm:flex-row gap-4 sm:gap-2">
                        <ClearableTextField name="host" label={t("host")} />
                        <ClearableTextField name="path" label={t("path")} />
                    </div>
                    <EarlyDataField />
                    <HttpHeadersDynamicFields />
                </SettingSection>
                <SettingSection
                    value="split-http"
                    triggerText={t("page.hosts.split-http-settings")}
                >
                    <SplitHttpFields />
                </SettingSection>
                <SettingSection
                    value="camouflage"
                    triggerText={t("page.hosts.camouflage-settings")}
                >
                    <div className="space-y-4 sm:space-y-6">
                        <FragmentField />
                        <NoiseField />
                    </div>
                </SettingSection>
                <SettingSection
                    value="mux"
                    triggerText={t("page.hosts.mux-settings")}
                >
                    <MuxSettingsFields />
                </SettingSection>
                <SettingSection
                    value="security"
                    triggerText={t("page.hosts.security-settings")}
                >
                    <SecurityFields />
                </SettingSection>
            </Accordion>
        </div>
    );
};

export * from "./schema";
export * from "./split-http-settings.schema";
export * from "./default";
