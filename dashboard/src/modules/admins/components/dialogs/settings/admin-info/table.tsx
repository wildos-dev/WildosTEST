import * as React from "react";
import {
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Table,
    TableBody,
    TableRowWithCell,
} from "@wildosvpn/common/components";
import {
    type AdminProp,
    AdminEnabledPill,
    AdminPermissionPill,
    useAdminUsersStatusDisable,
    useAdminUsersStatusEnable,
    AdminTokenButton
} from "@wildosvpn/modules/admins";
import { useTranslation } from "react-i18next";
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { format } from '@chbphone55/pretty-bytes';
import { useAuth } from "@wildosvpn/modules/auth";

export const AdminInfoTable: React.FC<AdminProp> = ({ admin: entity }) => {
    const { t } = useTranslation();
    const usersDataUsage = format(entity.users_data_usage);
    const { mutate: adminStatusEnable, isPending: enablePending } = useAdminUsersStatusEnable()
    const { mutate: adminStatusDisable, isPending: disablePending } = useAdminUsersStatusDisable()
    const auth = useAuth()
    
    // Check if this is the current user with robust JWT validation
    const isCurrentUser = () => {
        const token = auth.getAuthToken();
        if (!token || typeof token !== 'string') return false;
        
        try {
            // Validate JWT format: header.payload.signature
            const parts = token.split('.');
            if (parts.length !== 3) return false;
            
            // Validate payload part exists and is not empty
            const payloadPart = parts[1];
            if (!payloadPart) return false;
            
            // Validate base64 format by trying to decode
            const payload = JSON.parse(atob(payloadPart));
            
            // Validate payload structure
            if (!payload || typeof payload !== 'object') return false;
            if (!payload.sub || typeof payload.sub !== 'string') return false;
            
            return payload.sub === entity.username;
        } catch (error) {
            // Log error for debugging (only in development)
            if (import.meta.env.DEV) {
                console.warn('JWT validation failed:', error);
            }
            return false;
        }
    };

    const handleAdmingStatusEnable = React.useCallback(() => {
        adminStatusEnable({ admin: entity })
    }, [entity, adminStatusEnable]);

    const handleAdmingStatusDisable = React.useCallback(() => {
        adminStatusDisable({ admin: entity })
    }, [entity, adminStatusDisable]);

    return (
        <Card>
            <CardHeader className="flex flex-row justify-between items-center w-full">
                <CardTitle>{t("admin_info")}</CardTitle>
                <div className="hstack justify-center items-center gap-2">
                    <Button
                        className={"bg-destructive rounded-2xl"}
                        onClick={handleAdmingStatusDisable}
                    >
                        {disablePending ? <Icon name="Loader" className="animate-spin" /> : (<><Icon name="UserX" className="mr-2" /> {t('page.admins.disable_users')} </>)}
                    </Button>
                    <Button
                        className="bg-success rounded-2xl"
                        onClick={handleAdmingStatusEnable}
                    >
                        {enablePending ? <Icon name="Loader" className="animate-spin" /> : (<><Icon name="UserCheck" className="mr-2" /> {t('page.admins.enable_users')} </>)}
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableBody>
                        <TableRowWithCell label={t("username")} value={entity.username} />
                        <TableRowWithCell
                            label={t("enabled")}
                            value={<AdminEnabledPill admin={entity} />}
                        />
                        <TableRowWithCell
                            label={t("page.admins.permission")}
                            value={<AdminPermissionPill admin={entity} />}
                        />
                        <TableRowWithCell
                            label={t("page.admins.users-data-usage")}
                            value={`${usersDataUsage[0]} ${usersDataUsage[1]}`}
                        />
                        {isCurrentUser() && (
                            <TableRowWithCell
                                label={t("page.admins.token.copy")}
                                value={<AdminTokenButton />}
                            />
                        )}

                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
};
