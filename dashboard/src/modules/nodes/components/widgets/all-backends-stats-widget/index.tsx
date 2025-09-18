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

const chartConfig = {
    running: {
        label: "Running",
        color: "#10b981",
    },
    stopped: {
        label: "Stopped",
        color: "#ef4444",
    },
} satisfies ChartConfig;

interface AllBackendsStatsProps {
    totalBackends: number;
    runningBackends: number;
    stoppedBackends: number;
    totalNodes: number;
    nodesWithData: number;
}

export const AllBackendsStatsWidget: React.FC<AllBackendsStatsProps> = ({ 
    totalBackends, 
    runningBackends, 
    stoppedBackends,
    totalNodes,
    nodesWithData 
}) => {
    const { t } = useTranslation();

    const stats = [
        { type: "running", total: runningBackends, fill: "var(--color-running)" },
        { type: "stopped", total: stoppedBackends, fill: "var(--color-stopped)" },
    ]

    return (
        <SectionWidget
            title={<> <Icon name="Layers" /> {t('all-backends', 'All Backends')} </>}
            description={t('page.home.all-backends-stats.desc', 'Backend services status across all nodes')}
            className="h-full"
        >
            <div className="flex flex-col gap-4">
                {/* Main Chart */}
                <ChartContainer
                    config={chartConfig}
                    className="mx-auto aspect-square min-h-[250px] w-full"
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
                            innerRadius={50}
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
                                                    className="fill-foreground text-2xl font-bold"
                                                >
                                                    {totalBackends || 0}
                                                </tspan>
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={(viewBox.cy || 0) + 20}
                                                    className="fill-muted-foreground text-sm"
                                                >
                                                    {t('backends', 'Backends')}
                                                </tspan>
                                            </text>
                                        )
                                    }
                                }}
                            />
                        </Pie>
                        <ChartLegend className="flex -translate-y-2 flex-wrap gap-2 [&>*]:basis-1/3 [&>*]:justify-center text-sm" content={<ChartLegendContent />} />
                    </PieChart>
                </ChartContainer>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-center p-2 rounded bg-muted/30">
                        <div className="font-semibold text-foreground">{nodesWithData}/{totalNodes}</div>
                        <div className="text-muted-foreground">{t('active-nodes', 'Active Nodes')}</div>
                    </div>
                    <div className="text-center p-2 rounded bg-muted/30">
                        <div className="font-semibold text-green-600">{runningBackends}</div>
                        <div className="text-muted-foreground">{t('running', 'Running')}</div>
                    </div>
                </div>
            </div>
        </SectionWidget>
    );
};