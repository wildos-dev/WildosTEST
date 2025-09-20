import * as React from "react";
import {
    DialogTitle,
    DialogContent,
    Dialog,
    DialogHeader,
    DialogDescription,
    Form,
    FormItem,
    FormControl,
    FormMessage,
    FormLabel,
    Input,
    FormField,
    Button,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    FormDescription,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import {
    NodeSchema,
    useNodesCreationMutation,
    useNodesUpdateMutation,
} from "../..";
import type { NodeType } from "../..";
import { useMutationDialog, MutationDialogProps } from "@wildosvpn/common/hooks";
import { useNodeConfigQuery } from "@wildosvpn/modules/settings";

export const MutationDialog: React.FC<MutationDialogProps<NodeType>> = ({
    entity,
    onClose,
}) => {
    const updateMutation = useNodesUpdateMutation();
    const createMutation = useNodesCreationMutation();
    const { t } = useTranslation();
    const { data: nodeConfig } = useNodeConfigQuery();

    const defaultValue = React.useMemo(() => ({
        id: 0,
        name: "",
        address: "",
        status: "none",
        port: nodeConfig.port,
        usage_coefficient: 1,
        connection_backend: "grpclib",
    }), [nodeConfig.port]);

    const { onOpenChange, open, form, handleSubmit } = useMutationDialog({
        entity,
        onClose,
        schema: NodeSchema,
        createMutation,
        updateMutation,
        defaultValue,
    });

    return (
        <Dialog open={open} onOpenChange={onOpenChange} defaultOpen={true}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle className="text-primary">
                        {entity
                            ? t("page.nodes.dialogs.edition.title")
                            : t("page.nodes.dialogs.creation.title")}
                    </DialogTitle>
                    <DialogDescription>
                        {entity 
                            ? t("page.nodes.dialogs.edition.description")
                            : t("page.nodes.dialogs.creation.description")}
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={handleSubmit}>
                        <FormField
                            control={form.control}
                            name="name"
                            render={({ field }) => (
                                <FormItem className="w-full">
                                    <FormLabel>{t("name")}</FormLabel>
                                    <FormControl>
                                        <Input {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <div className="flex flex-col sm:flex-row gap-4 sm:gap-2 sm:items-end">
                            <FormField
                                control={form.control}
                                name="address"
                                render={({ field }) => (
                                    <FormItem className="flex-1 sm:w-2/3">
                                        <FormLabel>{t("address")}</FormLabel>
                                        <FormControl>
                                            <Input {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="port"
                                render={({ field }) => (
                                    <FormItem className="w-full sm:w-1/3">
                                        <FormLabel>{t("port")}</FormLabel>
                                        <FormControl>
                                            <Input type="number" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>
                        <div className="flex flex-col sm:flex-row gap-4 sm:gap-2 sm:items-start">
                            <FormField
                                control={form.control}
                                name="connection_backend"
                                render={({ field }) => (
                                    <FormItem className="flex-1">
                                        <FormLabel>{t("page.nodes.connection_backend")}</FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
                                        >
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder={t("placeholders.nodes-connection")} />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value="grpclib">grpclib</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <FormDescription>
                                            {t("page.nodes.connection_backend_desc")}
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="usage_coefficient"
                                render={({ field }) => (
                                    <FormItem className="w-full sm:w-1/2">
                                        <FormLabel>{t("page.nodes.usage_coefficient")}</FormLabel>
                                        <FormControl>
                                            <Input {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
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
            </DialogContent>
        </Dialog>
    );
};
