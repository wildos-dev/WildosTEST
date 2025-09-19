import * as React from 'react';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import {
    SectionWidget,
    ChartConfig,
    ChartContainer,
    ChartTooltip,
} from "@wildosvpn/common/components";
import { Bar, BarChart, XAxis, YAxis } from "recharts";
import { useAggregateHostSystemMetricsQuery } from "@wildosvpn/modules/nodes/api/aggregate-metrics.query";

const chartConfig = {
    cpu: {
        label: "CPU",
        color: "#3b82f6",
    },
    memory: {
        label: "Memory",
        color: "#10b981",
    },
    disk: {
        label: "Disk",
        color: "#f59e0b",
    },
} satisfies ChartConfig;

export const HostSystemMetricsWidget: React.FC = () => {
    const { t } = useTranslation();
    const { data: metricsData, isLoading, error } = useAggregateHostSystemMetricsQuery();

    if (error) {
        return (
            <SectionWidget
                title={<><Icon name="Monitor" /> {t('host-system-metrics', 'Host System Metrics')}</>}
                description={t('host-system-metrics.desc', 'Aggregated system metrics across all nodes')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('error-loading-metrics', 'Error loading system metrics')}
                </div>
            </SectionWidget>
        );
    }

    if (isLoading) {
        return (
            <SectionWidget
                title={<><Icon name="Monitor" /> {t('host-system-metrics', 'Host System Metrics')}</>}
                description={t('host-system-metrics.desc', 'Aggregated system metrics across all nodes')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('loading', 'Loading...')}
                </div>
            </SectionWidget>
        );
    }

    const chartData = [
        {
            name: t('cpu', 'CPU'),
            value: Math.round(metricsData.averageCpuUsage),
            fill: "var(--color-cpu)",
            icon: (props: any) => <Icon name="Activity" {...props} />,
        },
        {
            name: t('memory', 'Memory'),
            value: Math.round(metricsData.averageMemoryUsage),
            fill: "var(--color-memory)",
            icon: (props: any) => <Icon name="Activity" {...props} />,
        },
        {
            name: t('disk', 'Disk'),
            value: Math.round(metricsData.averageDiskUsage),
            fill: "var(--color-disk)",
            icon: (props: any) => <Icon name="HardDrive" {...props} />,
        },
    ];

    // Helper function to format bytes
    const formatBytes = (bytes: string) => {
        const num = parseInt(bytes) || 0;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        if (num === 0) return '0 B';
        const i = Math.floor(Math.log(num) / Math.log(1024));
        return Math.round((num / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <SectionWidget
            title={<><Icon name="Monitor" /> {t('host-system-metrics', 'Host System Metrics')}</>}
            description={t('host-system-metrics.desc', 'Aggregated system metrics across all nodes')}
            className="h-full"
        >
            <div className="flex flex-col gap-6 w-full">
                {/* Resource Usage Chart */}
                <div className="w-full">
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">
                        {t('average-resource-usage', 'Average Resource Usage (%)')}
                    </h4>
                    <ChartContainer
                        config={chartConfig}
                        className="mx-auto w-full aspect-[5/3]"
                    >
                        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <XAxis 
                                dataKey="name" 
                                axisLine={false}
                                tickLine={false}
                                className="text-xs fill-muted-foreground"
                            />
                            <YAxis 
                                domain={[0, 100]}
                                axisLine={false}
                                tickLine={false}
                                className="text-xs fill-muted-foreground"
                            />
                            <ChartTooltip
                                content={({ active, payload }: { active?: boolean; payload?: any[] }) => {
                                    if (active && payload && payload.length) {
                                        return (
                                            <div className="bg-background border rounded p-2 shadow-md">
                                                <p className="text-sm">
                                                    <span className="font-medium">{payload[0].payload.name}:</span>
                                                    <span className="ml-1">{payload[0].value}%</span>
                                                </p>
                                            </div>
                                        );
                                    }
                                    return null;
                                }}
                            />
                            <Bar dataKey="value" radius={4} />
                        </BarChart>
                    </ChartContainer>
                </div>

                {/* Summary Statistics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Monitor" className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="font-semibold text-foreground">
                            {metricsData.activeNodes}/{metricsData.totalNodes}
                        </div>
                        <div className="text-muted-foreground">
                            {t('active-nodes', 'Active Nodes')}
                        </div>
                    </div>
                    
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Activity" className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="font-semibold text-green-600">
                            {metricsData.healthyNodes}
                        </div>
                        <div className="text-muted-foreground">
                            {t('healthy', 'Healthy')}
                        </div>
                    </div>
                    
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Activity" className="h-4 w-4 text-red-600" />
                        </div>
                        <div className="font-semibold text-red-600">
                            {metricsData.criticalNodes}
                        </div>
                        <div className="text-muted-foreground">
                            {t('critical', 'Critical')}
                        </div>
                    </div>
                    
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Network" className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="font-semibold text-foreground">
                            {formatBytes(metricsData.totalNetworkTx)}
                        </div>
                        <div className="text-muted-foreground">
                            {t('total-tx', 'Total TX')}
                        </div>
                    </div>
                </div>
            </div>
        </SectionWidget>
    );
};