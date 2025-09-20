import * as React from 'react';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
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

const buildNodesChartConfig = (t: any): ChartConfig => ({
    healthy: {
        label: t("healthy"),
        color: "#10b981",
    },
    unhealthy: {
        label: t("unhealthy"),
        color: "#ef4444",
    },
});

interface NodesStatsProps {
    total: number;
    healthy: number;
    unhealthy: number;
}

export const NodesStatsWidget: React.FC<NodesStatsProps> = ({ total, healthy, unhealthy }) => {
    const { t, i18n } = useTranslation();
    
    const chartConfig = React.useMemo(() => buildNodesChartConfig(t), [i18n.language]);

    const stats = [
        { type: "healthy", total: healthy, fill: "var(--color-healthy)" },
        { type: "unhealthy", total: unhealthy, fill: "var(--color-unhealthy)" },
    ]

    return (
        <SectionWidget
            title={<> <Icon name="Server" /> {t('nodes')} </>}
            description={t('page.home.nodes-stats.desc')}
            className="h-full"
        >
            <ChartContainer
                config={chartConfig}
                className="mx-auto aspect-square w-full"
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
                        innerRadius={60}
                        strokeWidth={5}
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
                                                className="fill-foreground text-3xl font-bold"
                                            >
                                                {total || 0}
                                            </tspan>
                                            <tspan
                                                x={viewBox.cx}
                                                y={(viewBox.cy || 0) + 24}
                                                className="fill-muted-foreground"
                                            >
                                                {t('nodes')}
                                            </tspan>
                                        </text>
                                    )
                                }
                            }}
                        />
                    </Pie>
                    <ChartLegend className="flex -translate-y-2 flex-wrap gap-2 [&>*]:basis-1/5 [&>*]:justify-center text-md" content={<ChartLegendContent />} />
                </PieChart>
            </ChartContainer>
        </SectionWidget>
    );
};