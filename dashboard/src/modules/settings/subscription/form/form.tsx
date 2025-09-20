import { zodResolver } from "@hookform/resolvers/zod";
import { useFieldArray, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { schema } from "./schema";
import { RuleItem } from "./rule-item";
import {
    Button,
    Form,
    Sortable,
    ScrollArea,
    Label,
    Separator,
    Awaiting,
    CheckboxField,
} from "@wildosvpn/common/components";
import { Schema } from "./schema"
import { Overlay } from "./overlay"
import {
    ProfileTitleField,
    SupportLinkField,
    UpdateIntervalField,
    PlaceholderRemarkField,
} from "./fields";
import { NoRulesAlert } from "./no-rules-alert";
import {
    useSubscriptionSettingsQuery,
    useSubscriptionSettingsMutation,
} from "@wildosvpn/modules/settings/subscription";
import * as React from 'react';

export function SubscriptionRulesForm() {
    const { t } = useTranslation()
    const { data, isFetching } = useSubscriptionSettingsQuery()
    const subscriptionSettings = useSubscriptionSettingsMutation()
    const form = useForm<Schema>({
        resolver: zodResolver(schema),
        defaultValues: data,
    })

    const handleResetLocalChanges = React.useCallback(
        () => {
            form.reset(data)
        },
        [form, data],
    )

    const handleSubscriptionRulesDataUpdate = React.useCallback(
        () => {
            form.reset(data, {
                keepDirtyValues: true
            })
        },
        [form, data],
    )

    React.useEffect(() => {
        if (data) {
            handleSubscriptionRulesDataUpdate()
        }
    }, [data, handleSubscriptionRulesDataUpdate])

    const onSubmit = (data: Schema) => {
        subscriptionSettings.mutate(data)
    }

    const { fields, append, move, remove } = useFieldArray({
        control: form.control,
        name: "rules"
    })

    return (
        <Form {...form}>
            <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="flex w-full max-w-4xl flex-col space-y-4 sm:space-y-6"
            >
                <div className="space-y-4 sm:space-y-6">
                    <ProfileTitleField />
                    <div className="flex flex-col sm:flex-row gap-4 sm:gap-6">
                        <UpdateIntervalField />
                        <SupportLinkField />
                    </div>
                    <CheckboxField
                        name="template_on_acceptance"
                        label={t("page.settings.subscription-settings.template-on-acceptance")}
                    />
                    <PlaceholderRemarkField />
                    <CheckboxField
                        name="placeholder_if_disabled"
                        label={t("page.settings.subscription-settings.placeholder-if-disabled")}
                    />
                    <CheckboxField
                        name="shuffle_configs"
                        label={t("page.settings.subscription-settings.shuffle-configs")}
                    />
                </div>
                <Separator className="my-4 sm:my-6" />
                <div className="space-y-2 sm:space-y-3">
                    <h4 className="text-lg sm:text-xl font-semibold">
                        {t("page.settings.subscription-settings.subscription-title")}
                    </h4>
                    <p className="text-sm sm:text-base text-muted-foreground">
                        {t("page.settings.subscription-settings.subscription-desc")}
                    </p>
                </div>
                <Awaiting
                    isFetching={isFetching}
                    Skeleton={
                        <>
                            <Overlay />
                            <Overlay />
                            <Overlay />
                            <Overlay />
                        </>
                    }
                    isNotFound={fields.length === 0}
                    NotFound={<NoRulesAlert />}
                    Component={
                        <div className="space-y-1">
                            <Sortable
                                value={fields}
                                onMove={({ activeIndex, overIndex }) =>
                                    move(activeIndex, overIndex)
                                }
                            >
                                <div className="grid grid-cols-[2fr,1.3fr,0.25fr,0.25fr] items-center justify-start gap-2 my-2">
                                    <Label className="font-semibold">
                                        {t("pattern")}
                                    </Label>
                                    <Label className="font-semibold">
                                        {t("result")}
                                    </Label>
                                </div>
                                <ScrollArea className="flex flex-col w-full max-h-[400px] gap-2" type="always">
                                    {fields.map((field, index) => (
                                        <RuleItem
                                            field={field}
                                            index={index}
                                            onRemove={remove} />
                                    ))}
                                </ScrollArea>
                            </Sortable>
                        </div>
                    }
                />
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 sm:justify-end pt-4 sm:pt-6 border-t">
                    <Button
                        type="button"
                        variant="destructive"
                        className="w-full h-12 sm:h-auto sm:w-auto text-sm sm:text-base"
                        onMouseDown={handleResetLocalChanges}
                    >
                        {t("page.settings.subscription-settings.reset-local-changes")}
                    </Button>
                    <Button
                        type="button"
                        variant="outline"
                        className="w-full h-12 sm:h-auto sm:w-auto text-sm sm:text-base"
                        onClick={() =>
                            append({
                                pattern: "",
                                result: "block",
                            })
                        }
                    >
                        {t("page.settings.subscription-settings.add-rule")}
                    </Button>
                    <Button 
                        type="submit" 
                        className="w-full h-12 sm:h-auto sm:w-auto text-sm sm:text-base font-semibold"
                    >
                        {t("submit")}
                    </Button>
                </div>
            </form>
        </Form>
    )
}
