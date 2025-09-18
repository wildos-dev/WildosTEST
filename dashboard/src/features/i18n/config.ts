import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpApi from 'i18next-http-backend';
import { initReactI18next } from 'react-i18next';
import { setDefaultOptions } from 'date-fns';
import { enUS, ru } from 'date-fns/locale';

declare module 'i18next' {
    interface CustomTypeOptions {
        returnNull: false;
    }
}

// Initialize i18next with React integration
export const initializeI18nCore = () => {
    return i18n
        .use(LanguageDetector)
        .use(HttpApi)
        .use(initReactI18next)
        .init({
            debug: import.meta.env.DEV,
            fallbackLng: 'en',
            interpolation: {
                escapeValue: false,
            },
            load: 'languageOnly',
            detection: {
                order: ['localStorage', 'sessionStorage', 'cookie', 'navigator'],
                lookupLocalStorage: 'i18nextLng',
                lookupSessionStorage: 'i18nextLng',
                lookupCookie: 'i18nextLng',
                caches: ['localStorage', 'sessionStorage', 'cookie'],
            },
            backend: {
                loadPath: `/locales/{{lng}}.json`,
                requestOptions: {
                    cache: 'no-cache'
                }
            },
            supportedLngs: ['en', 'ru'],
            react: {
                useSuspense: false,
            },
            // Принудительно сохранять язык
            saveMissing: false,
            updateMissing: false,
            // Более строгие настройки для предотвращения fallback
            nonExplicitSupportedLngs: false,
        })
        .then(() => {
            // Set date-fns locale based on language
            const locale = i18n.language === 'ru' ? ru : enUS;
            setDefaultOptions({ locale });
            document.documentElement.lang = i18n.language;
            console.log('✅ i18n initialized with translations loaded');
        })
        .catch((error) => {
            console.error('❌ i18n initialization failed:', error);
        });
};

// Set up language change handler
export const setupLanguageHandler = () => {
    i18n.on('languageChanged', (lng) => {
        console.log(`🔄 Language changed to: ${lng}`);
        // Set date-fns locale based on language
        const locale = lng === 'ru' ? ru : enUS;
        setDefaultOptions({ locale });
        document.documentElement.lang = lng;
        
        // Принудительно сохраняем выбранный язык
        localStorage.setItem('i18nextLng', lng);
        sessionStorage.setItem('i18nextLng', lng);
        
        // Проверяем, что ресурсы загружены
        if (!i18n.hasResourceBundle(lng, 'translation')) {
            console.warn(`⚠️ Resources not loaded for ${lng}, forcing reload...`);
            i18n.reloadResources(lng).then(() => {
                console.log(`✅ Resources reloaded for ${lng}`);
            });
        }
    });
    
    // Add error logging for failed resource loading
    i18n.on('failedLoading', (lng, ns, msg) => {
        console.error(`❌ Failed to load translations for ${lng}/${ns}:`, msg);
    });
    
    // Добавляем обработчик успешной загрузки
    i18n.on('loaded', (loaded) => {
        console.log(`✅ Translations loaded:`, loaded);
    });
};

export default i18n;