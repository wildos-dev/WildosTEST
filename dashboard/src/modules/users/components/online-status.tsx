import * as React from "react"
import { useTranslation } from "react-i18next"
import { cn } from "@wildosvpn/common/utils"
import { UserType, isUserOnline } from "@wildosvpn/modules/users"
import { Tooltip, TooltipContent, TooltipTrigger } from "@wildosvpn/common/components"
import { Icon } from "@wildosvpn/common/components/ui/icon"

interface OnlineStatusProps {
    user: UserType
}

export const OnlineStatus: React.FC<OnlineStatusProps> = ({ user }) => {
    let statusColor
    let tooltip
    const status = isUserOnline(user)
    const { t } = useTranslation()
    if (user.online_at === null) {
        statusColor = "text-yellow-500"
        tooltip = t('not_connected')
    } else if (status) {
        statusColor = "text-green-500"
        tooltip = t('online')
    } else {
        statusColor = "text-red-500"
        tooltip = t('offline')
    }
    return (
        <Tooltip>
            <TooltipTrigger>
                <Icon name="Circle" className={cn("w-5 h-5", statusColor)} />
            </TooltipTrigger>
            <TooltipContent>
                {tooltip}
            </TooltipContent>
        </Tooltip>
    )
}
