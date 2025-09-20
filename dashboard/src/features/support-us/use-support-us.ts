import { SupportUsVariation } from './types'
import * as React from 'react';
import { useLocalStorage } from "@uidotdev/usehooks";

export const useSupportUs = (
    variant: SupportUsVariation, defaultValue: boolean
): [boolean, React.Dispatch<React.SetStateAction<boolean>>] => {
    const [local, setLocal] = useLocalStorage<boolean>("wildosvpn-support-us", defaultValue);
    const [state, setState] = React.useState<boolean>(defaultValue)
    return variant === "local-storage" ? [local, setLocal] : [state, setState]
}
