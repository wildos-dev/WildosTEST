
import { SectionWidget } from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";

export const ConfigurationWidget = () => {
    const { t } = useTranslation();
    
    return (
        <SectionWidget description="" title={t('common.system_configuration')}>
            Config fields
        </SectionWidget>
    )
}
