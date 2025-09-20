import * as React from "react"
import { Loading } from "@wildosvpn/common/components/loading"

// Simple dynamic import for recharts
const useRecharts = () => {
    const [recharts, setRecharts] = React.useState<any>(null)
    
    React.useEffect(() => {
        import("recharts").then(setRecharts)
    }, [])
    
    return recharts
}

import { cn } from "@wildosvpn/common/utils/cn"
import { SafeChartContainer } from "@wildosvpn/common/components/safe-chart-container"

// Color validation utility to prevent XSS attacks
function isValidCSSColor(color: string): boolean {
    // Prevent potentially dangerous characters that could be used for CSS injection
    const dangerousChars = /[;{}@"'<>\\]/
    if (dangerousChars.test(color)) {
        return false
    }
    
    // Enforce reasonable length limit to prevent DoS
    if (color.length > 200) {
        return false
    }
    
    // Check parentheses balance to prevent malformed CSS
    let parenCount = 0
    for (const char of color) {
        if (char === '(') parenCount++
        else if (char === ')') parenCount--
        if (parenCount < 0) return false
    }
    if (parenCount !== 0) return false
    
    // Allow common safe patterns:
    // - Hex colors: #fff, #ffffff, #ffffffff
    // - RGB/HSL functions with various syntaxes: rgb(255,0,0), rgb(255 0 0 / 0.5)
    // - CSS variables: var(--color), var(--chart-1)
    // - Nested patterns: hsl(var(--chart-1)), rgb(var(--accent) / 0.5)
    // - Named colors: red, blue, transparent, currentColor
    const colorPatterns = [
        // Hex colors
        /^#[0-9a-fA-F]{3,8}$/,
        // RGB/RGBA functions - allow nested parentheses for var() functions
        /^rgba?\(\s*(?:[^()]+|\([^()]*\))*\s*\)$/,
        // HSL/HSLA functions - allow nested parentheses for var() functions
        /^hsla?\(\s*(?:[^()]+|\([^()]*\))*\s*\)$/,
        // CSS variables
        /^var\(\s*--[\w-]+\s*(?:,\s*[^)]+)?\s*\)$/,
        // Named colors (basic allowlist)
        /^(?:transparent|currentColor|inherit|initial|unset|revert|red|green|blue|black|white|gray|grey)$/i,
    ]
    
    return colorPatterns.some(pattern => pattern.test(color.trim()))
}

// Sanitize color value to prevent injection attacks
function sanitizeColor(color: string | undefined): string | null {
    if (!color || typeof color !== 'string') {
        return null
    }
    const trimmedColor = color.trim()
    const isValid = isValidCSSColor(trimmedColor)
    
    // Add development warning when colors are filtered out
    if (!isValid && import.meta.env.DEV) {
        console.warn(`ChartStyle: Filtered out potentially unsafe color value: "${trimmedColor}"`)
    }
    
    return isValid ? trimmedColor : null
}

// Safely escape CSS selector ID to prevent CSS injection
function escapeCSSSelector(id: string): string {
    // Remove or replace potentially problematic characters in CSS selectors
    return id.replace(/[^A-Za-z0-9_-]/g, '')
}

// Format: { THEME_NAME: CSS_SELECTOR }
const THEMES = { light: "", dark: ".dark" } as const

export type ChartConfig = {
    [k in string]: {
        label?: React.ReactNode
        icon?: React.ComponentType
    } & (
        | { color?: string; theme?: never }
        | { color?: never; theme: Record<keyof typeof THEMES, string> }
    )
}

type ChartContextProps = {
    config: ChartConfig
}

// Safe createContext with fallback
const ChartContext = (React?.createContext || (() => {
    throw new Error("React is not available - check React imports and build configuration");
}))<ChartContextProps | null>(null)

function useChart() {
    const context = (React?.useContext || (() => {
        throw new Error("React is not available - check React imports and build configuration");
    }))(ChartContext)

    if (!context) {
        throw new Error("useChart must be used within a <ChartContainer />")
    }

    return context
}

// Lazy loading wrapper for ResponsiveContainer
const LazyRechartsContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const recharts = useRecharts()
    
    if (!recharts) {
        return <Loading />
    }
    
    return (
        <recharts.ResponsiveContainer>
            {children}
        </recharts.ResponsiveContainer>
    )
}

const ChartContainer = React.forwardRef<
    HTMLDivElement,
    React.ComponentProps<"div"> & {
        config: ChartConfig
        children: React.ReactNode
    }
>(({ id, className, children, config, ...props }, ref) => {
    const uniqueId = React.useId()
    const rawChartId = `chart-${id || uniqueId.replace(/:/g, "")}`
    // Sanitize the chartId to ensure consistency with CSS selector
    const chartId = escapeCSSSelector(rawChartId)

    return (
        <ChartContext.Provider value={{ config }}>
            <div
                data-chart={chartId}
                ref={ref}
                className={cn(
                    "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none",
                    className
                )}
                {...props}
            >
                <ChartStyle id={chartId} config={config} />
                <SafeChartContainer
                    fallback={
                        <div className="flex items-center justify-center h-full">
                            <div className="animate-pulse">
                                <div className="h-4 bg-gray-200 rounded w-32 mb-4 mx-auto"></div>
                                <div className="space-y-2">
                                    <div className="h-3 bg-gray-200 rounded w-24 mx-auto"></div>
                                    <div className="h-3 bg-gray-200 rounded w-20 mx-auto"></div>
                                </div>
                            </div>
                        </div>
                    }
                >
                    <LazyRechartsContainer>
                        {children}
                    </LazyRechartsContainer>
                </SafeChartContainer>
            </div>
        </ChartContext.Provider>
    )
})
ChartContainer.displayName = "Chart"

const ChartStyle = ({ id, config }: { id: string; config: ChartConfig }) => {
    const colorConfig = Object.entries(config).filter(
        ([, config]) => config.theme || config.color
    )

    if (!colorConfig.length) {
        return null
    }

    // Generate safe CSS content with sanitized colors
    const cssContent = Object.entries(THEMES)
        .map(([theme, prefix]) => {
            const colorVars = colorConfig
                .map(([key, itemConfig]) => {
                    const color =
                        itemConfig.theme?.[theme as keyof typeof itemConfig.theme] ||
                        itemConfig.color
                    
                    // Sanitize the color value to prevent XSS
                    const sanitizedColor = sanitizeColor(color)
                    if (!sanitizedColor) {
                        return null
                    }
                    
                    // Ensure key contains only safe characters (alphanumeric, hyphen, underscore)
                    const safeKey = key.replace(/[^a-zA-Z0-9\-_]/g, '')
                    return `  --color-${safeKey}: ${sanitizedColor};`
                })
                .filter(Boolean)
                .join('\n')
            
            if (!colorVars) {
                return ''
            }
            
            return `${prefix} [data-chart="${id}"] {\n${colorVars}\n}`
        })
        .filter(Boolean)
        .join('\n')

    if (!cssContent) {
        return null
    }

    // Safety limit to prevent DoS via huge CSS content
    const MAX_CSS_CONTENT_LENGTH = 10000
    if (cssContent.length > MAX_CSS_CONTENT_LENGTH) {
        if (import.meta.env.DEV) {
            console.warn(`ChartStyle: CSS content too large (${cssContent.length} chars), truncating to prevent DoS`)
        }
        // Truncate but try to preserve complete CSS rules
        const truncated = cssContent.substring(0, MAX_CSS_CONTENT_LENGTH)
        const lastBrace = truncated.lastIndexOf('}')
        const safeCssContent = lastBrace > 0 ? truncated.substring(0, lastBrace + 1) : ''
        return safeCssContent ? <style>{safeCssContent}</style> : null
    }

    return <style>{cssContent}</style>
}

// Dynamic import approach for tooltip
const ChartTooltip = React.forwardRef<any, any>((props, ref) => {
    const recharts = useRecharts()
    
    if (!recharts) {
        return null
    }
    
    return <recharts.Tooltip {...props} ref={ref} />
})

const ChartTooltipContent = React.forwardRef<
    HTMLDivElement,
    any &
    React.ComponentProps<"div"> & {
        hideLabel?: boolean
        hideIndicator?: boolean
        indicator?: "line" | "dot" | "dashed"
        nameKey?: string
        labelKey?: string
        valueFormatter?: (value: any) => string
    }
>(
    (
        {
            active,
            payload,
            className,
            indicator = "dot",
            hideLabel = false,
            hideIndicator = false,
            label,
            labelFormatter,
            valueFormatter,
            labelClassName,
            formatter,
            color,
            nameKey,
            labelKey,
        },
        ref
    ) => {
        const { config } = useChart()

        const tooltipLabel = React.useMemo(() => {
            if (hideLabel || !payload?.length) {
                return null
            }

            const [item] = payload
            if (!item) {
                return null
            }
            
            const key = `${labelKey || item.dataKey || item.name || "value"}`
            const itemConfig = getPayloadConfigFromPayload(config, item, key)
            const value =
                !labelKey && typeof label === "string"
                    ? config[label as keyof typeof config]?.label || label
                    : itemConfig?.label

            if (labelFormatter) {
                return (
                    <div className={cn("font-medium", labelClassName)}>
                        {labelFormatter(value, payload)}
                    </div>
                )
            }

            if (!value) {
                return null
            }

            return <div className={cn("font-medium", labelClassName)}>{value}</div>
        }, [
            label,
            labelFormatter,
            payload,
            hideLabel,
            labelClassName,
            config,
            labelKey,
        ])

        if (!active || !payload?.length) {
            return null
        }

        const nestLabel = payload.length === 1 && indicator !== "dot"

        return (
            <div
                ref={ref}
                className={cn(
                    "grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl",
                    className
                )}
            >
                {!nestLabel ? tooltipLabel : null}
                <div className="grid gap-1.5">
                    {payload.map((item: any, index: number) => {
                        const key = `${nameKey || item.name || item.dataKey || "value"}`
                        const itemConfig = getPayloadConfigFromPayload(config, item, key)
                        const indicatorColor = color || item.payload.fill || item.color

                        return (
                            <div
                                key={item.dataKey}
                                className={cn(
                                    "flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground",
                                    indicator === "dot" && "items-center"
                                )}
                            >
                                {formatter && item?.value !== undefined && item.name ? (
                                    formatter(item.value, item.name, item, index, item.payload)
                                ) : (
                                    <>
                                        {itemConfig?.icon ? (
                                            <itemConfig.icon />
                                        ) : (
                                            !hideIndicator && (
                                                <div
                                                    className={cn(
                                                        "shrink-0 rounded-[2px] border-[--color-border] bg-[--color-bg]",
                                                        {
                                                            "h-2.5 w-2.5": indicator === "dot",
                                                            "w-1": indicator === "line",
                                                            "w-0 border-[1.5px] border-dashed bg-transparent":
                                                                indicator === "dashed",
                                                            "my-0.5": nestLabel && indicator === "dashed",
                                                        }
                                                    )}
                                                    style={
                                                        {
                                                            "--color-bg": indicatorColor,
                                                            "--color-border": indicatorColor,
                                                        } as React.CSSProperties
                                                    }
                                                />
                                            )
                                        )}
                                        <div
                                            className={cn(
                                                "flex flex-1 justify-between leading-none",
                                                nestLabel ? "items-end" : "items-center"
                                            )}
                                        >
                                            <div className="grid gap-1.5">
                                                {nestLabel ? tooltipLabel : null}
                                                <span className="text-muted-foreground">
                                                    {itemConfig?.label || item.name}
                                                </span>
                                            </div>
                                            {item.value && (
                                                <span className="font-mono font-medium tabular-nums text-foreground">
                                                    {valueFormatter ? valueFormatter(item.value) : item.value.toLocaleString()}
                                                </span>
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>
                        )
                    })}
                </div>
            </div>
        )
    }
)
ChartTooltipContent.displayName = "ChartTooltip"

// Dynamic import approach for legend
const ChartLegend = React.forwardRef<any, any>((props, ref) => {
    const recharts = useRecharts()
    
    if (!recharts) {
        return null
    }
    
    return <recharts.Legend {...props} ref={ref} />
})

const ChartLegendContent = React.forwardRef<
    HTMLDivElement,
    React.ComponentProps<"div"> & {
        payload?: any[];
        verticalAlign?: "top" | "bottom";
        hideIcon?: boolean
        nameKey?: string
    }
>(
    (
        { className, hideIcon = false, payload, verticalAlign = "bottom", nameKey },
        ref
    ) => {
        const { config } = useChart()

        if (!payload?.length) {
            return null
        }

        return (
            <div
                ref={ref}
                className={cn(
                    "flex items-center justify-center gap-4",
                    verticalAlign === "top" ? "pb-3" : "pt-3",
                    className
                )}
            >
                {payload.map((item, index) => {
                    const key = `${nameKey || item.dataKey || "value"}`
                    const itemConfig = getPayloadConfigFromPayload(config, item, key)

                    return (
                        <div
                            key={`${key}-${index}`}
                            className={cn(
                                "flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:text-muted-foreground"
                            )}
                        >
                            {itemConfig?.icon && !hideIcon ? (
                                <itemConfig.icon />
                            ) : (
                                <div
                                    className="h-2 w-2 shrink-0 rounded-[2px]"
                                    style={{
                                        backgroundColor: item.color,
                                    }}
                                />
                            )}
                            {itemConfig?.label}
                        </div>
                    )
                })}
            </div>
        )
    }
)
ChartLegendContent.displayName = "ChartLegend"

// Helper to extract item config from a payload.
function getPayloadConfigFromPayload(
    config: ChartConfig,
    payload: unknown,
    key: string
) {
    if (typeof payload !== "object" || payload === null) {
        return undefined
    }

    const payloadPayload =
        "payload" in payload &&
            typeof payload.payload === "object" &&
            payload.payload !== null
            ? payload.payload
            : undefined

    let configLabelKey: string = key

    if (
        key in payload &&
        typeof payload[key as keyof typeof payload] === "string"
    ) {
        configLabelKey = payload[key as keyof typeof payload] as string
    } else if (
        payloadPayload &&
        key in payloadPayload &&
        typeof payloadPayload[key as keyof typeof payloadPayload] === "string"
    ) {
        configLabelKey = payloadPayload[
            key as keyof typeof payloadPayload
        ] as string
    }

    return configLabelKey in config
        ? config[configLabelKey]
        : config[key as keyof typeof config]
}

export {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
    ChartStyle,
}
