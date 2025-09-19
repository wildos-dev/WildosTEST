import * as React from 'react';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import {
    SectionWidget,
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
} from "@wildosvpn/common/components";
import { Label, Pie, PieChart } from "recharts"

const buildUsersChartConfig = (t: any): ChartConfig => ({
    active: {
        label: t("active"),
        color: "#3b82f6",
    },
    online: {
        label: t("online"),
        color: "#10b981",
    },
    expired: {
        label: t("expired"),
        color: "#4b5563",
    },
    onHold: {
        label: t("on_hold"),
        color: "#A855F7",
    },
    limited: {
        label: t("limited"),
        color: "#ef4444",
    },
});

interface UsersStatsProps {
    limited: number;
    active: number;
    expired: number;
    on_hold: number;
    online: number;
    total: number;
}

export const UsersStatsWidget: React.FC<UsersStatsProps> = ({ total, limited, active, expired, on_hold, online }) => {
    const { t, i18n } = useTranslation();
    const isMobile = !useScreenBreakpoint('md');
    
    const chartConfig = React.useMemo(() => buildUsersChartConfig(t), [i18n.language]);

    const stats = [
        { type: "limited", total: limited, fill: "var(--color-limited)" },
        { type: "active", total: active, fill: "var(--color-active)" },
        { type: "expired", total: expired, fill: "var(--color-expired)" },
        { type: "onHold", total: on_hold, fill: "var(--color-onHold)" },
        { type: "online", total: online, fill: "var(--color-online)" },
    ]

    return (
        <SectionWidget
            title={<> <Icon name="Users" className="h-5 w-5" /> {t('users')} </>}
            description={t('page.home.users-stats.desc')}
            className="w-full h-full"
        >
            <div className="flex flex-col space-y-4">
                {/* Mobile: Show key metrics as cards above chart */}
                {isMobile && (
                    <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="text-center p-2 bg-muted/50 rounded">
                            <div className="font-semibold text-lg">{total || 0}</div>
                            <div className="text-muted-foreground">{t('total')}</div>
                        </div>
                        <div className="text-center p-2 bg-muted/50 rounded">
                            <div className="font-semibold text-lg text-green-600">{online || 0}</div>
                            <div className="text-muted-foreground">{t('online')}</div>
                        </div>
                    </div>
                )}
                
                <ChartContainer
                    config={chartConfig}
                    className={isMobile 
                        ? "mx-auto w-full aspect-[4/3]" // Better responsive ratio
                        : "mx-auto aspect-square w-full"
                    }
                >
                    <PieChart>
                        <ChartTooltip
                            cursor={false}
                            content={<ChartTooltipContent hideLabel />}
                        />
                        <Pie
                            data={stats}
                            dataKey="total"
                            nameKey="type"
                            innerRadius={isMobile ? 40 : 60}
                            strokeWidth={isMobile ? 3 : 5}
                        >
                            <Label
                                content={({ viewBox }) => {
                                    if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                                        return (
                                            <text
                                                x={viewBox.cx}
                                                y={viewBox.cy}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                            >
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={viewBox.cy}
                                                    className={`fill-foreground font-bold ${
                                                        isMobile ? 'text-xl' : 'text-3xl'
                                                    }`}
                                                >
                                                    {total || 0}
                                                </tspan>
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={(viewBox.cy || 0) + (isMobile ? 16 : 24)}
                                                    className={`fill-muted-foreground ${
                                                        isMobile ? 'text-xs' : 'text-sm'
                                                    }`}
                                                >
                                                    {t('users')}
                                                </tspan>
                                            </text>
                                        )
                                    }
                                }}
                            />
                        </Pie>
                        <ChartLegend 
                            className={isMobile 
                                ? "flex -translate-y-2 flex-wrap gap-1 [&>*]:basis-1/3 [&>*]:justify-center text-xs" 
                                : "flex -translate-y-2 flex-wrap gap-2 [&>*]:basis-1/5 [&>*]:justify-center text-md"
                            } 
                            content={<ChartLegendContent />} 
                        />
                    </PieChart>
                </ChartContainer>
            </div>
        </SectionWidget>
    );
};

