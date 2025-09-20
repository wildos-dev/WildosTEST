import {
    DropdownMenuSub,
    DropdownMenuSubContent,
    DropdownMenuItem,
    DropdownMenuSubTrigger,
    DropdownMenuPortal
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components";
import * as React from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@wildosvpn/common/utils";

const LanguageItem = ({ language, title }: { language: string, title: string }) => {
    const { i18n } = useTranslation();

    const changeLanguage = async (lang: string) => {
        try {
            console.log(`🔄 Switching to language: ${lang}`);
            
            // Проверяем, что ресурсы загружены
            if (!i18n.hasResourceBundle(lang, 'translation')) {
                console.log(`📥 Loading resources for ${lang}...`);
                await i18n.loadLanguages(lang);
            }
            
            // Меняем язык
            await i18n.changeLanguage(lang);
            
            // Принудительно сохраняем
            localStorage.setItem('i18nextLng', lang);
            
            console.log(`✅ Language switched to: ${lang}, current: ${i18n.language}`);
        } catch (error) {
            console.error(`❌ Failed to change language to ${lang}:`, error);
        }
    };
    return (
        <DropdownMenuItem
            className={cn({ "bg-primary text-secondary": i18n.language === language })}
            onClick={() => changeLanguage(language)}
        >
            {title}
        </DropdownMenuItem>
    );
}

export const LanguageSwitchMenu: React.FC = () => {
    const { t } = useTranslation();

    return (
        <DropdownMenuSub>
            <DropdownMenuSubTrigger arrowDir="left">
                <div className="hstack items-center gap-2 w-full justify-end">
                    <span>{t("language")}</span>
                    <Icon name="Languages" className="size-[1rem]" />
                </div>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
                <DropdownMenuSubContent>
                    <LanguageItem language="en" title={t("languages.english")} />
                    <LanguageItem language="ru" title={t("languages.russian")} />
                </DropdownMenuSubContent>
            </DropdownMenuPortal>
        </DropdownMenuSub>
    );
};
