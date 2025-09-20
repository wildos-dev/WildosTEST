import iconImage from '../../../assets/icon.png';
import { useTranslation } from 'react-i18next';

export const HeaderLogo = () => {
    const { t } = useTranslation();
    return (
        <div className="flex justify-center items-center p-2 h-10 rounded-lg">
            <img 
                src={iconImage} 
                alt={t('logo.wildos-icon')} 
                className="h-8 w-8 object-contain"
            />
        </div>
    );
}
