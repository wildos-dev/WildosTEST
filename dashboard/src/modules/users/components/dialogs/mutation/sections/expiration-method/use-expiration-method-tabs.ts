import * as React from 'react';
import { UserMutationType, ExpireStrategy } from "@wildosvpn/modules/users";
import { useFormContext } from "react-hook-form";
import { strategies } from "./expiration-method.strategy"


export const useExpirationMethodTabs = (entity: UserMutationType | null) => {
    const form = useFormContext();

    const [
        selectedExpirationMethodTab,
        setSelectedExpirationMethodTab
    ] = React.useState<ExpireStrategy>(entity ? entity.expire_strategy : 'fixed_date');
    React.useEffect(() => {
        strategies[selectedExpirationMethodTab as ExpireStrategy].apply(form);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedExpirationMethodTab]);

    const handleTabChange = (value: string) => {
        setSelectedExpirationMethodTab(value as ExpireStrategy);
    };

    return {
        selectedExpirationMethodTab,
        setSelectedExpirationMethodTab,
        handleTabChange,
    };
};
