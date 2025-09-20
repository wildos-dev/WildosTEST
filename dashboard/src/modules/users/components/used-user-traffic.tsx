import * as React from 'react'
import { UserType } from '@wildosvpn/modules/users';
import { format } from '@chbphone55/pretty-bytes';
import { useTranslation } from 'react-i18next';


interface UserUsedTrafficProps {
    user: UserType
}

export const UserUsedTraffic: React.FC<UserUsedTrafficProps> = (
    { user }
) => {
    const { t } = useTranslation()
    const formattedUsedTraffic = format(user.used_traffic)
    const formattedDatalimit = (user.data_limit != null) ? format(user.data_limit) : []
    return (
        <div className="flex gap-x-5 justify-start items-center">
            <div className="flex flex-col items-center space-y-1">
                <div className="relative w-12 h-12">
                    <svg className="w-12 h-12 transform -rotate-90" viewBox="0 0 36 36">
                        <path
                            className="text-gray-300"
                            stroke="currentColor"
                            strokeWidth="3"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                            className="text-blue-600"
                            stroke="currentColor"
                            strokeWidth="3"
                            strokeDasharray={`${user.data_limit ? (user.used_traffic / user.data_limit * 100) : 0}, 100`}
                            strokeLinecap="round"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-xs text-gray-700 dark:text-gray-300">
                        {user.data_limit ? `${Math.round((user.used_traffic / user.data_limit * 100))}%` : '0%'}
                    </span>
                </div>
            </div>
            <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
                    {formattedUsedTraffic[0]} {formattedUsedTraffic[1]}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500">
                    {user.data_limit ? `${formattedDatalimit[0]} ${formattedDatalimit[1]}` : t('page.users.unlimited')}
                </p>
            </div>
        </div>
    );
}
