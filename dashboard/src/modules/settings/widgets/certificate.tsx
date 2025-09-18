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
        >
            <CertificateButton />
        </MiniWidget>
    )
}
