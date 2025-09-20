import {
    Alert,
    AlertDescription,
    AlertTitle,
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { useTranslation } from "react-i18next";

export const NoRulesAlert = () => {
    const { t } = useTranslation()
    return (
        <Alert>
            <Icon name="Info" className="mr-2" />
            <AlertTitle className="font-semibold text-primary">{t('page.settings.subscription-settings.alert.title')}</AlertTitle>
            <AlertDescription>
                {t('page.settings.subscription-settings.alert.desc')}
            </AlertDescription>
        </Alert>
    )
}
