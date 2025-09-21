import * as React from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    Form,
    Button,
    ScrollArea,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import { useDialog } from "@wildosvpn/common/hooks";
import { UseFormReturn } from "react-hook-form";

export interface UnifiedMutationDialogProps<T = any> {
    /** Entity to edit (null for creation) */
    entity?: T | null;
    /** Dialog close handler */
    onClose: () => void;
    /** Form instance from react-hook-form */
    form: UseFormReturn<any>;
    /** Form submit handler */
    onSubmit: (data: any) => void;
    /** Dialog title for creation mode */
    createTitle: string;
    /** Dialog title for edit mode */
    editTitle: string;
    /** Dialog description for creation mode */
    createDescription: string;
    /** Dialog description for edit mode */
    editDescription: string;
    /** Form fields to render */
    children: React.ReactNode;
    /** Whether form is submitting */
    isSubmitting?: boolean;
    /** Submit button text (defaults to translated "submit") */
    submitText?: string;
    /** Custom dialog content className */
    contentClassName?: string;
    /** Whether to show scroll area (default: true) */
    scrollable?: boolean;
    /** Maximum dialog width class (default: "md:max-w-[32rem]") */
    maxWidth?: string;
}

export const UnifiedMutationDialog: React.FC<UnifiedMutationDialogProps> = ({
    entity,
    onClose,
    form,
    onSubmit,
    createTitle,
    editTitle,
    createDescription,
    editDescription,
    children,
    isSubmitting = false,
    submitText,
    contentClassName = "h-screen max-w-full md:h-auto p-4 sm:p-6",
    scrollable = true,
    maxWidth = "md:max-w-[32rem]",
}) => {
    const { t } = useTranslation();
    const [open, onOpenChange] = useDialog(true);

    React.useEffect(() => {
        if (!open) onClose();
    }, [open, onClose]);

    const isEditing = entity !== null && entity !== undefined;
    const title = isEditing ? editTitle : createTitle;
    const description = isEditing ? editDescription : createDescription;

    const handleSubmit = (data: any) => {
        onSubmit(data);
        onOpenChange(false);
    };

    const dialogContent = (
        <>
            <DialogHeader className="mb-4 sm:mb-6">
                <DialogTitle className="text-lg sm:text-xl text-primary">
                    {t(title)}
                </DialogTitle>
                <DialogDescription className="text-sm sm:text-base">
                    {t(description)}
                </DialogDescription>
            </DialogHeader>
            
            <Form {...form}>
                <form 
                    onSubmit={form.handleSubmit(handleSubmit)} 
                    className="flex flex-col h-full"
                >
                    <div className="flex-1">
                        {children}
                    </div>
                    <div className="mt-4 sm:mt-6 pt-4 border-t">
                        <Button
                            className="w-full h-12 sm:h-auto sm:w-auto sm:min-w-[120px] font-semibold"
                            type="submit"
                            disabled={isSubmitting || form.formState.isSubmitting}
                            aria-label={submitText || t("submit")}
                        >
                            {submitText || t("submit")}
                        </Button>
                    </div>
                </form>
            </Form>
        </>
    );

    return (
        <Dialog open={open} onOpenChange={onOpenChange} defaultOpen={true}>
            <DialogContent className={`${maxWidth} ${contentClassName}`}>
                {scrollable ? (
                    <ScrollArea className="flex flex-col h-full">
                        {dialogContent}
                    </ScrollArea>
                ) : (
                    dialogContent
                )}
            </DialogContent>
        </Dialog>
    );
};