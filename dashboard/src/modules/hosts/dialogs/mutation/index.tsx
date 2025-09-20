import * as React from "react";
import {
    Button,
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    Form,
    ScrollArea,
} from "@wildosvpn/common/components";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import {
    type HostWithProfileSchemaType,
    type HostWithProfileType,
    useHostsCreationMutation,
    useHostsUpdateMutation,
} from "@wildosvpn/modules/hosts";
import { type MutationDialogProps, useDialog } from "@wildosvpn/common/hooks";
import { ProtocolType } from "@wildosvpn/modules/inbounds";
import { useProfileStrategy } from "./profiles";
import {
    transformToDictionary,
    transformToFields,
} from "@wildosvpn/libs/dynamic-field";

// Pipe utility for function composition
const pipe = <T,>(...fns: Array<(arg: T) => T>) => (value: T): T =>
    fns.reduce((acc, fn) => fn(acc), value);

// Port adapter interface for bidirectional transformation
interface PortAdapter<TForm, TApi> {
    toApi: (value: TForm) => TApi;
    fromApi: (value: TApi) => TForm;
}

// Individual field transformers using port-adapter pattern
const alpnPortAdapter: PortAdapter<string, string> = {
    toApi: (value: string) => value === "none" ? "" : value,
    fromApi: (value: string) => value === "" ? "none" : value,
};

const fingerprintPortAdapter: PortAdapter<string, string> = {
    toApi: (value: string) => value === "none" ? "" : value,
    fromApi: (value: string) => value === "" ? "none" : value,
};

const portPortAdapter: PortAdapter<string | number, number | null> = {
    toApi: (value: string | number) => value === "" ? null : Number(value),
    fromApi: (value: number | null) => value === null ? "" : String(value),
};

// HTTP headers duplex adapter with bidirectional transformation
const httpHeadersPortAdapter: PortAdapter<any, any> = {
    toApi: (headers: any) => headers ? transformToDictionary(headers) : undefined,
    fromApi: (headers: any) => headers ? transformToFields(headers) : undefined,
};

// Transformation functions using function composition
const transformAlpn = (values: any) => ({
    ...values,
    alpn: values.alpn ? alpnPortAdapter.toApi(values.alpn) : values.alpn,
});

const transformFingerprint = (values: any) => ({
    ...values,
    fingerprint: values.fingerprint ? fingerprintPortAdapter.toApi(values.fingerprint) : values.fingerprint,
});

const transformPort = (values: any) => ({
    ...values,
    port: values.port !== undefined ? portPortAdapter.toApi(values.port) : values.port,
});

const transformHttpHeadersToApi = (values: any) => ({
    ...values,
    http_headers: httpHeadersPortAdapter.toApi(values.http_headers),
});

const transformHttpHeadersFromApi = (values: any) => ({
    ...values,
    http_headers: httpHeadersPortAdapter.fromApi(values.http_headers),
});

// Composed transformers
const formToApiTransformer = pipe(
    transformAlpn,
    transformFingerprint,
    transformPort,
    transformHttpHeadersToApi,
);

const apiToFormTransformer = pipe(
    transformHttpHeadersFromApi,
);

interface HostMutationDialogProps
    extends MutationDialogProps<HostWithProfileType> {
    inboundId?: number;
    protocol?: ProtocolType;
}

// Legacy functions replaced with composed transformers above
// formToApiTransformer: transforms form data to API format
// apiToFormTransformer: transforms API data to form format

export const HostsMutationDialog: React.FC<HostMutationDialogProps> = ({
    entity,
    inboundId,
    onClose,
    protocol,
}) => {
    const [open, onOpenChange] = useDialog(true);
    const [Schema, ProfileFields, defaultValue] = useProfileStrategy(protocol);
    const form = useForm<HostWithProfileSchemaType>({
        defaultValues: entity ? apiToFormTransformer(entity) : defaultValue,
        resolver: zodResolver(Schema),
    });
    const updateMutation = useHostsUpdateMutation();
    const createMutation = useHostsCreationMutation();
    const { t } = useTranslation();

    const submit = (values: HostWithProfileSchemaType) => {
        const host = formToApiTransformer(values);
        if (entity && entity.id !== undefined) {
            updateMutation.mutate({ hostId: entity.id, host });
            onOpenChange(false);
        } else if (inboundId !== undefined) {
            createMutation.mutate({ inboundId, host });
            onOpenChange(false);
        }
    };

    React.useEffect(() => {
        if (!open) onClose();
    }, [open, onClose]);

    React.useEffect(() => {
        if (entity) form.reset(apiToFormTransformer(entity));
        else form.reset(defaultValue);
    }, [entity, form, open, defaultValue]);

    return (
        <Dialog open={open} onOpenChange={onOpenChange} defaultOpen={true}>
            <DialogContent className="md:max-w-[32rem] lg:max-w-[40rem]">
                <ScrollArea className="flex flex-col h-full p-4 sm:p-6">
                    <DialogHeader className="mb-4 sm:mb-6">
                        <DialogTitle className="text-lg sm:text-xl text-primary">
                            {entity
                                ? t("page.hosts.dialogs.edition.title")
                                : t("page.hosts.dialogs.creation.title")}
                        </DialogTitle>
                        <DialogDescription className="text-sm sm:text-base">
                            {entity
                                ? t("page.hosts.dialogs.edition.description")
                                : t("page.hosts.dialogs.creation.description")}
                        </DialogDescription>
                    </DialogHeader>
                    <Form {...form}>
                        <form
                            onSubmit={form.handleSubmit(submit)}
                            className="h-full flex flex-col justify-between space-y-4 sm:space-y-6"
                        >
                            <div className="flex-1">
                                <ProfileFields />
                            </div>
                            <Button
                                className="w-full h-12 sm:h-auto sm:w-auto font-semibold mt-6"
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
