import * as React from "react";
import {
    DialogTitle,
    DialogContent,
    Dialog,
    DialogHeader,
    DialogDescription,
    Form,
    Button,
    ScrollArea,
    VStack,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import {
    useAdminsCreationMutation,
    useAdminsUpdateMutation,
    AdminEditSchema,
    AdminCreateSchema,
    AdminType,
} from "@wildosvpn/modules/admins";
import { ServicesField } from "@wildosvpn/modules/services";
import { UsernameField } from "@wildosvpn/modules/users";
import {
    PasswordField,
    EnabledField,
    ModifyUsersAccessField,
    SubscriptionUrlPrefixField,
    SudoPrivilageField,
    AllServicesAccessField,
} from "./fields";
import { useMutationDialog, MutationDialogProps } from "@wildosvpn/common/hooks";

export const AdminsMutationDialog: React.FC<MutationDialogProps<AdminType>> = ({
    onClose,
    entity = null,
}) => {
    const { t } = useTranslation();

    const defaultValue = React.useMemo(() => ({
        service_ids: [],
        username: "",
        is_sudo: false,
        enabled: true,
        modify_users_access: true,
    }), [])

    const { onOpenChange, open, form, handleSubmit } = useMutationDialog({
        entity,
        onClose,
        createMutation: useAdminsCreationMutation(),
        updateMutation: useAdminsUpdateMutation(),
        schema: entity ? AdminEditSchema : AdminCreateSchema,
        defaultValue,
    });

    const [change, setChange] = React.useState<boolean>(entity === null);
    if (entity !== null)
        form.setValue("password", null,
            {
                shouldTouch: true,
                shouldDirty: true,
            });

    return (
        <Dialog open={open} onOpenChange={onOpenChange} defaultOpen={true}>
            <DialogContent className="h-screen max-w-full md:h-auto md:max-w-[32rem] p-4 sm:p-6">
                <DialogHeader className="mb-4 sm:mb-6">
                    <DialogTitle className="text-lg sm:text-xl text-primary">
                        {t(entity ? "page.admins.dialogs.edition.title" : "page.admins.dialogs.creation.title")}
                    </DialogTitle>
                    <DialogDescription className="text-sm sm:text-base">
                        {t(entity ? "page.admins.dialogs.edition.description" : "page.admins.dialogs.creation.description")}
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={handleSubmit} className="flex flex-col h-full">
                        <ScrollArea className="flex-1 -mx-4 sm:-mx-6 px-4 sm:px-6">
                            <div className="flex flex-col space-y-4 sm:space-y-6">
                                <div className="space-y-4 sm:space-y-6">
                                    <UsernameField disabled={!!entity} />
                                    <PasswordField change={change} handleChange={setChange} />
                                    <SubscriptionUrlPrefixField />
                                    <EnabledField />
                                    <ModifyUsersAccessField />
                                    <SudoPrivilageField />
                                    <AllServicesAccessField />
                                </div>
                                <VStack className="space-y-4 sm:space-y-6">
                                    <ServicesField />
                                </VStack>
                            </div>
                        </ScrollArea>
                        <div className="mt-4 sm:mt-6 pt-4 border-t">
                            <Button
                                className="w-full h-12 sm:h-auto sm:w-auto sm:min-w-[120px] font-semibold"
                                type="submit"
                                disabled={form.formState.isSubmitting}
                            >
                                {t("submit")}
                            </Button>
                        </div>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
};
