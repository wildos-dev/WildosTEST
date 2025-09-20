import * as React from "react"

export type Theme = "dark"

type ThemeProviderProps = {
    children: React.ReactNode
}

// Simplified provider - always dark theme
export const ThemeProvider: React.FC<React.PropsWithChildren<ThemeProviderProps>> = ({ children }) => {
    React.useEffect(() => {
        // Guard against SSR and ensure browser environment
        if (typeof window === 'undefined' || !window.document) return;
        
        // Ensure dark theme is always applied
        const root = window.document.documentElement
        root.classList.remove("light")
        root.classList.add("dark")
    }, [])

    return <>{children}</>
}

// Simplified hook - always returns dark theme
export const useTheme = () => {
    return {
        theme: "dark" as const,
        setTheme: () => {} // No-op since theme is fixed
    }
}
