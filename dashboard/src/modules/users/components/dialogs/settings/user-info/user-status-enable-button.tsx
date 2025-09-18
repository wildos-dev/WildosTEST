import { Button } from "@wildosvpn/common/components";
import { cn } from "@wildosvpn/common/utils";
import { UserType, useUserStatusEnable } from "@wildosvpn/modules/users";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import * as React from "react";
import { useTranslation } from "react-i18next";

interface UserStatusEnableButtonProps {
    user: UserType;
}

export const UserStatusEnableButton: React.FC<UserStatusEnableButtonProps> = ({ user }) => {
    const [userStatus, setUserStatus] = React.useState<boolean>(user.enabled)
    const { t } = useTranslation()
    const { mutate: userStatusEnable, isPending } = useUserStatusEnable()

    const handleUserStatusEnabledToggle = React.useCallback(() => {
        const tempUserStatus = userStatus;
        userStatusEnable({ user: user, enabled: !userStatus })
        setUserStatus(!tempUserStatus)
    }, [user, userStatus, userStatusEnable]);

    const bgColor = isPending ? 'bg-muted-foreground' : (userStatus ? 'bg-destructive' : 'bg-success')

    return (
        <Button
            className={cn(bgColor, "rounded-2xl")}
            onClick={handleUserStatusEnabledToggle}
        >
            {!userStatus ? <Icon name="UserCheck" className="mr-2" /> : <Icon name="UserX" className="mr-2" />}
            {isPending ? <Icon name="Loader" className="animate-spin" /> : t(!userStatus ? 'enable' : 'disable')}
        </Button>
    )
}
