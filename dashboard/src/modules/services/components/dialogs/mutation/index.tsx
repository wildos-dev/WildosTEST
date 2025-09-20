import {
    DialogTitle,
    DialogContent,
    Dialog,
    DialogHeader,
    DialogDescription,
    Form,
    Button,
} from "@wildosvpn/common/components";
import * as React from 'react';
import {
    type ServiceType,
    useServicesCreationMutation,
    useServicesUpdateMutation,
} from "@wildosvpn/modules/services";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { useMutationDialog, MutationDialogProps } from "@wildosvpn/common/hooks";
import { NameField, InboundsField } from "./fields";

export const ServiceSchema = z.object({
    id: z.number().optional(),
    inbound_ids: z.array(z.number()).refine((value) => value.some((item) => item), {
        message: "validation.services.min_one_inbound",
    }),
    name: z.string().trim().min(1),
});

export const MutationDialog: React.FC<MutationDialogProps<ServiceType>> = ({
    entity,
    onClose,
}) => {
    const defaultValue = React.useMemo(() => ({
        name: "",
        inbound_ids: [],
    }), []);
    const updateMutation = useServicesUpdateMutation();
    const createMutation = useServicesCreationMutation();
    const { open, onOpenChange, form, handleSubmit } = useMutationDialog({
        onClose,
        entity,
        updateMutation,
        createMutation,
        defaultValue,
        schema: ServiceSchema,
    });
    const { t } = useTranslation();

    return (
        <Dialog open={open} onOpenChange={onOpenChange} defaultOpen={true}>
            <DialogContent className="h-screen max-w-full sm:h-auto sm:max-w-md md:max-w-lg lg:max-w-xl">
                <DialogHeader>
                    <DialogTitle className="text-primary">
                        {entity
                            ? t("page.services.dialogs.edition.title")
                            : t("page.services.dialogs.creation.title")}
                    </DialogTitle>
                    <DialogDescription>
                        {entity
                            ? t("page.services.dialogs.edition.description")
                            : t("page.services.dialogs.creation.description")}
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={handleSubmit} className="h-full flex flex-col">
                        <div className="flex-1 space-y-6 overflow-y-auto">
                            <div className="space-y-4 p-1">
                                <NameField />
                                <InboundsField />
                            </div>
                        </div>
                        <div className="flex-shrink-0 pt-6 border-t">
                            <Button
                                className="w-full h-12 font-semibold text-base"
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
