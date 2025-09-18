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
            <DialogContent className="min-w-full h-full md:h-auto md:min-w-[42rem]">
                <ScrollArea className="flex flex-col justify-between h-full ">
                    <DialogHeader className="mb-3">
                        <DialogTitle className="text-primary">
                            {t(entity ? "page.admins.dialogs.edition.title" : "page.admins.dialogs.creation.title")}
                        </DialogTitle>
                        <DialogDescription>
                            {t(entity ? "page.admins.dialogs.edition.description" : "page.admins.dialogs.creation.description")}
                        </DialogDescription>
                    </DialogHeader>
                    <Form {...form}>
                        <form onSubmit={handleSubmit} >
                            <div className="flex-col grid-cols-2 gap-2 sm:flex md:grid h-full">
                                <div className="space-y-3">
                                    <UsernameField disabled={!!entity} />
                                    <PasswordField change={change} handleChange={setChange} />
                                    <SubscriptionUrlPrefixField />
                                    <EnabledField />
                                    <ModifyUsersAccessField />
                                    <SudoPrivilageField />
                                    <AllServicesAccessField />
                                </div>
                                <VStack>
                                    <ServicesField />
                                </VStack>
                            </div>
                            <Button
                                className="mt-3 w-full font-semibold"
                                type="submit"
                                disabled={form.formState.isSubmitting}
                            >
                                {t("submit")}
                            </Button>
                        </form>
                    </Form>
                </ScrollArea>
            </DialogContent>
        </Dialog>
    );
};
