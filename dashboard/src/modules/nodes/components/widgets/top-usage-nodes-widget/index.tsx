import * as React from 'react';
import { Icon, CommonIcons } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import {
    SectionWidget,
    ChartConfig,
    ChartContainer,
    ChartTooltip,
} from "@wildosvpn/common/components";
import { Bar, BarChart, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { useTopUsageNodesQuery } from "@wildosvpn/modules/nodes/api/aggregate-metrics.query";

const chartConfig = {
    traffic: {
        label: "Traffic",
        color: "#3b82f6",
    },
} satisfies ChartConfig;

export const TopUsageNodesWidget: React.FC = () => {
    const { t } = useTranslation();
    const { data: topNodes, isLoading, error } = useTopUsageNodesQuery(5);

    // Helper function to format bytes
    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
    };

    // Helper function to format node name for chart display
    const formatNodeName = (name: string) => {
        return name.length > 12 ? name.substring(0, 10) + '...' : name;
    };

    if (error) {
        return (
            <SectionWidget
                title={<><Icon name="TrendingUp" /> {t('top-usage-nodes', 'Top Usage Nodes')}</>}
                description={t('top-usage-nodes.desc', 'Nodes with highest traffic usage (last 24h)')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('error-loading-usage', 'Error loading usage data')}
                </div>
            </SectionWidget>
        );
    }

    if (isLoading) {
        return (
            <SectionWidget
                title={<><Icon name="TrendingUp" /> {t('top-usage-nodes', 'Top Usage Nodes')}</>}
                description={t('top-usage-nodes.desc', 'Nodes with highest traffic usage (last 24h)')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('loading', 'Loading...')}
                </div>
            </SectionWidget>
        );
    }

    if (topNodes.length === 0) {
        return (
            <SectionWidget
                title={<><Icon name="TrendingUp" /> {t('top-usage-nodes', 'Top Usage Nodes')}</>}
                description={t('top-usage-nodes.desc', 'Nodes with highest traffic usage (last 24h)')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-8">
                    <Icon name="Server" className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">{t('no-usage-data', 'No usage data available')}</p>
                    <p className="text-xs mt-1">{t('no-usage-data-desc', 'Node usage data will appear here once traffic starts flowing')}</p>
                </div>
            </SectionWidget>
        );
    }

    const chartData = topNodes.map((node, index) => ({
        name: formatNodeName(node.nodeName),
        fullName: node.nodeName,
        traffic: node.totalTraffic,
        percentage: node.usagePercent,
        rank: index + 1,
        uplink: node.uplink,
        downlink: node.downlink,
    }));

    const totalTraffic = topNodes.reduce((sum, node) => sum + node.totalTraffic, 0);

    return (
        <SectionWidget
            title={<><CommonIcons.TrendingUp /> {t('top-usage-nodes', 'Top Usage Nodes')}</>}
            description={t('top-usage-nodes.desc', 'Nodes with highest traffic usage (last 24h)')}
            className="h-full"
        >
            <div className="flex flex-col gap-4 w-full">
                {/* Traffic Chart */}
                <div className="w-full">
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">
                        {t('traffic-distribution', 'Traffic Distribution')}
                    </h4>
                    <ChartContainer
                        config={chartConfig}
                        className="w-full h-[200px]"
                    >
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart 
                                data={chartData} 
                                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                layout="horizontal"
                            >
                                <XAxis 
                                    type="number"
                                    axisLine={false}
                                    tickLine={false}
                                    className="text-xs fill-muted-foreground"
                                    tickFormatter={(value: number) => formatBytes(value)}
                                />
                                <YAxis 
                                    type="category"
                                    dataKey="name"
                                    axisLine={false}
                                    tickLine={false}
                                    className="text-xs fill-muted-foreground"
                                />
                                <ChartTooltip
                                    content={({ active, payload }: { active?: boolean; payload?: any[] }) => {
                                        if (active && payload && payload.length) {
                                            const data = payload[0].payload;
                                            return (
                                                <div className="bg-background border rounded p-3 shadow-md min-w-[200px]">
                                                    <p className="text-sm font-medium mb-2">{data.fullName}</p>
                                                    <div className="space-y-1 text-xs">
                                                        <p className="flex justify-between">
                                                            <span>Total Traffic:</span>
                                                            <span className="font-medium">{formatBytes(data.traffic)}</span>
                                                        </p>
                                                        <p className="flex justify-between">
                                                            <span>Usage:</span>
                                                            <span className="font-medium">{Math.round(data.percentage)}%</span>
                                                        </p>
                                                        <p className="flex justify-between items-center">
                                                            <span className="flex items-center gap-1">
                                                                <Icon name="ArrowUp" className="h-3 w-3" /> Uplink:
                                                            </span>
                                                            <span className="font-medium">{formatBytes(data.uplink)}</span>
                                                        </p>
                                                        <p className="flex justify-between items-center">
                                                            <span className="flex items-center gap-1">
                                                                <Icon name="ArrowDown" className="h-3 w-3" /> Downlink:
                                                            </span>
                                                            <span className="font-medium">{formatBytes(data.downlink)}</span>
                                                        </p>
                                                    </div>
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                                <Bar 
                                    dataKey="traffic" 
                                    fill="var(--color-traffic)"
                                    radius={[0, 4, 4, 0]}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartContainer>
                </div>

                {/* Node Ranking List */}
                <div className="space-y-2">
                    <h4 className="text-sm font-medium text-muted-foreground">
                        {t('detailed-ranking', 'Detailed Ranking')}
                    </h4>
                    <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {topNodes.map((node, index) => (
                            <div 
                                key={node.nodeId}
                                className="flex items-center justify-between p-3 rounded-lg border bg-muted/30"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold">
                                        #{index + 1}
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium text-foreground">
                                            {node.nodeName}
                                        </div>
                                        <div className="text-xs text-muted-foreground">
                                            Node ID: {node.nodeId}
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="text-right">
                                    <div className="text-sm font-medium text-foreground">
                                        {formatBytes(node.totalTraffic)}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                        {Math.round(node.usagePercent)}% of top usage
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Summary Statistics */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="font-semibold text-foreground">
                            {formatBytes(totalTraffic)}
                        </div>
                        <div className="text-muted-foreground">
                            {t('total-traffic', 'Total Traffic')}
                        </div>
                    </div>
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="font-semibold text-foreground">
                            {topNodes.length}
                        </div>
                        <div className="text-muted-foreground">
                            {t('active-nodes', 'Active Nodes')}
                        </div>
                    </div>
                </div>
            </div>
        </SectionWidget>
    );
};