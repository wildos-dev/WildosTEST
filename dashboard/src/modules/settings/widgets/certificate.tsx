import {
    MiniWidget
} from "@wildosvpn/common/components";
import {
    CertificateButton
} from "@wildosvpn/modules/settings";
import { useTranslation } from "react-i18next";

export const CertificateWidget = () => {
    const { t } = useTranslation()
    return (
        <MiniWidget
            title={t("certificate")}
            className="p-4 sm:p-6"
        >
            <div className="space-y-4 sm:space-y-6">
                <CertificateButton className="w-full h-12 sm:h-auto sm:w-auto text-sm sm:text-base" />
            </div>
        </MiniWidget>
    )
}
