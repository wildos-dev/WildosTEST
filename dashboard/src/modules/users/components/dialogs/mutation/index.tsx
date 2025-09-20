import * as React from 'react';
import {
    Separator,
    Form,
    Button,
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import {
    DATA_LIMIT_METRIC,
    useUsersCreationMutation,
    useUsersUpdateMutation,
    UserSchema,
    UsernameField,
    type UserMutationType,
} from "@wildosvpn/modules/users";
import { ServicesField } from "@wildosvpn/modules/services";
import { NoteField } from "./fields";
import { type MutationDialogProps, useMutationDialog } from "@wildosvpn/common/hooks";
import { DataLimitFields, ExpirationMethodFields } from "./sections";

export const UsersMutationDialog: React.FC<MutationDialogProps<UserMutationType>> = ({
    entity,
    onClose,
}) => {
    const { t } = useTranslation();
    const defaultValue = React.useMemo(
        () => ({
            service_ids: [],
            username: "",
            data_limit_reset_strategy: "no_reset",
            data_limit: undefined,
            note: "",
            expire_date: "",
            expire_strategy: "fixed_date",
        }),
        [],
    );

    const { open, onOpenChange, form, handleSubmit } = useMutationDialog({
        entity,
        onClose,
        createMutation: useUsersCreationMutation(),
        updateMutation: useUsersUpdateMutation(),
        schema: UserSchema,
        defaultValue,
        loadFormtter: (d) => ({
            ...d,
            data_limit: (d.data_limit ? d.data_limit : 0) / DATA_LIMIT_METRIC,
        }),
    });

    const isMobile = !useScreenBreakpoint('md');

    const footer = (
        <Button
            className="w-full font-semibold h-12 text-base"
            size={isMobile ? "lg" : "default"}
            type="submit"
            disabled={form.formState.isSubmitting}
            data-testid="button-submit-user"
        >
            {t("submit")}
        </Button>
    );

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl">
                <DialogHeader>
                    <DialogTitle>
                        {entity
                            ? t("page.users.dialogs.edition.title")
                            : t("page.users.dialogs.creation.title")}
                    </DialogTitle>
                </DialogHeader>
            <Form {...form}>
                <form onSubmit={handleSubmit} className="space-y-6 pb-4">
                    {/* Mobile: Single column layout, Desktop: Two column grid */}
                    <div className={isMobile 
                        ? "flex flex-col space-y-6" 
                        : "grid grid-cols-1 lg:grid-cols-2 gap-6"
                    }>
                        {/* Left column / Primary fields */}
                        <div className="space-y-6">
                            <div className="space-y-4">
                                <UsernameField disabled={!!entity?.username} />
                            </div>
                            <Separator className="my-4" />
                            
                            {/* Collapsible data limit section on mobile */}
                            <div className="space-y-4">
                                <DataLimitFields />
                            </div>
                            <Separator className="my-4" />
                            
                            {/* Collapsible expiration section on mobile */}
                            <div className="space-y-4">
                                <ExpirationMethodFields entity={entity} />
                            </div>
                            <Separator className="my-4" />
                            
                            <div className="space-y-4">
                                <NoteField />
                            </div>
                        </div>
                        
                        {/* Right column / Services */}
                        <div className={isMobile ? "mt-6" : ""}>
                            <div className="space-y-4">
                                <ServicesField />
                            </div>
                        </div>
                    </div>
                </form>
            </Form>
            <DialogFooter>
                {footer}
            </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};
