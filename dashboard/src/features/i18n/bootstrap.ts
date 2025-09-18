import i18n from './config';

// Initialize React i18next integration (simplified - React integration now happens in config.ts)
export const initializeReactI18n = async () => {
    try {
        // React integration is already handled in initializeI18nCore
        // Just ensure i18n is ready and resources are loaded
        const defaultNS = Array.isArray(i18n.options.defaultNS) 
            ? i18n.options.defaultNS[0] 
            : (i18n.options.defaultNS || 'translation');
        if (i18n.isInitialized && i18n.hasResourceBundle(i18n.language, defaultNS)) {
            console.log('✅ React i18n initialized successfully');
            return true;
        } else {
            console.warn('⚠ i18n initialized but translations may not be loaded yet');
            return true; // Still allow app to continue
        }
    } catch (error) {
        console.error('❌ React i18n initialization failed:', error);
        return false;
    }
};