import resolveConfig from "tailwindcss/resolveConfig";

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import tailwindConfig from "@wildosvpn/../tailwind.config.js";
import * as React from 'react';

const fullConfig = resolveConfig(tailwindConfig);
const screens = fullConfig?.theme?.screens || {};

export const useScreenBreakpoint = (query: keyof typeof screens): boolean => {
    const mediaQuery = `(min-width: ${screens[query]})`;
    const matchQueryList = window.matchMedia(mediaQuery);
    const [isMatch, setMatch] = React.useState<boolean>(false);
    const onChange = (e: MediaQueryListEvent) => setMatch(e.matches);
    React.useEffect(() => {
        setMatch(matchQueryList.matches);
        matchQueryList.addEventListener("change", onChange);
        return () => matchQueryList.removeEventListener("change", onChange);
    }, [query, matchQueryList]);
    return isMatch;
}
