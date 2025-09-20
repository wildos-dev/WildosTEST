import * as React from "react";
import {
  Awaiting,
  SettingsInfoSkeleton,
  SettingsDialogProps,
  SettingsDialog,
} from "@wildosvpn/common/components";
import { type AdminType } from "@wildosvpn/modules/admins";
import { AdminInfoTable } from "./admin-info";
import { useTranslation } from "react-i18next";

interface AdminsSettingsDialogProps extends SettingsDialogProps {
  entity: AdminType | null;
  onClose: () => void;
  isPending: boolean;
}

export const AdminsSettingsDialog: React.FC<AdminsSettingsDialogProps> = ({
  onOpenChange,
  open,
  entity,
  onClose,
  isPending,
}) => {
  const { t } = useTranslation();

  return (
    <SettingsDialog open={open} onClose={onClose} onOpenChange={onOpenChange}>
      <Awaiting
        Component={
          entity ? (
            <AdminInfoTable admin={entity} />
          ) : (
            <div>{t('not-found.admin')}</div>
          )
        }
        Skeleton={<SettingsInfoSkeleton />}
        isFetching={isPending}
      />
    </SettingsDialog>
  );
};

//
//           <Tabs defaultValue="info" className="w-full h-full">
//             <TabsList className="w-full bg-accent">
//               <TabsTrigger className="w-full" value="info">
//                 {t("admin_info")}
//               </TabsTrigger>
//               <TabsTrigger className="w-full" value="services">
//                 {t("services")}
//               </TabsTrigger>
//               <TabsTrigger className="w-full" value="subscription">
//                 {t("users")}
//               </TabsTrigger>
//             </TabsList>
//             <TabsContent
//               value="info"
//               className="flex flex-col gap-2 w-full h-full"
//             >
//               <AdminInfoTable admin={entity} />
//             </TabsContent>
//             {/* <TabsContent value="services"> */}
//               {/* <AdminServicesTable admin={entity} /> */}
//             {/* </TabsContent> */}
//             {/* <TabsContent value="users">Users</TabsContent> */}
//           </Tabs>
