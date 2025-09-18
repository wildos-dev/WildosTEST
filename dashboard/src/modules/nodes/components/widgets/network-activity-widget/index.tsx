import * as React from 'react';
import { Icon, CommonIcons } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import {
    SectionWidget,
    ChartConfig,
    ChartContainer,
    ChartTooltip,
} from "@wildosvpn/common/components";
import { Line, LineChart, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { useNetworkActivityQuery, useAggregateHostSystemMetricsQuery } from "@wildosvpn/modules/nodes/api/aggregate-metrics.query";


interface NetworkDataPoint {
    timestamp: string;
    rx: number;
    tx: number;
    time: number;
}

export const NetworkActivityWidget: React.FC = () => {
    const { t } = useTranslation();
    const { data: networkData, isLoading, error } = useNetworkActivityQuery();
    const { data: hostMetrics } = useAggregateHostSystemMetricsQuery();
    
    // Store historical data points for the chart
    const [historicalData, setHistoricalData] = React.useState<NetworkDataPoint[]>([]);
    
    // Localized chart config
    const chartConfigWithI18n = {
        rx: {
            label: t('network.rx'),
            color: "#10b981",
        },
        tx: {
            label: t('network.tx'),
            color: "#3b82f6",
        },
    } satisfies ChartConfig;

    // Helper function to format bytes
    const formatBytes = (bytes: number, decimals = 2) => {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return parseFloat((bytes / Math.pow(1024, i)).toFixed(decimals)) + ' ' + sizes[i];
    };

    // Helper function to format rate (bytes per second)
    const formatRate = (bytesPerSecond: number) => {
        return formatBytes(bytesPerSecond) + '/s';
    };

    // Update historical data every 15 seconds
    React.useEffect(() => {
        if (networkData && !isLoading && !error) {
            const now = new Date();
            const newDataPoint: NetworkDataPoint = {
                timestamp: now.toLocaleTimeString('en-US', { 
                    hour12: false, 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                }),
                rx: parseInt(networkData.totalRxBytes) || 0,
                tx: parseInt(networkData.totalTxBytes) || 0,
                time: now.getTime(),
            };

            setHistoricalData(prev => {
                const updated = [...prev, newDataPoint];
                // Keep only last 20 data points (5 minutes of data at 15-second intervals)
                return updated.slice(-20);
            });
        }
    }, [networkData, isLoading, error]);

    // Calculate rates based on historical data
    const currentRx = parseInt(networkData?.totalRxBytes || '0');
    const currentTx = parseInt(networkData?.totalTxBytes || '0');
    
    let rxRate = 0;
    let txRate = 0;
    
    if (historicalData.length >= 2) {
        const latest = historicalData[historicalData.length - 1];
        const previous = historicalData[historicalData.length - 2];
        
        if (latest && previous && typeof latest.time === 'number' && typeof previous.time === 'number') {
            const timeDiff = (latest.time - previous.time) / 1000; // seconds
            
            if (timeDiff > 0) {
                rxRate = Math.max(0, (latest.rx - previous.rx) / timeDiff);
                txRate = Math.max(0, (latest.tx - previous.tx) / timeDiff);
            }
        }
    }

    // Prepare chart data with rates
    const chartData = historicalData.slice(-10).map((point, index, arr) => {
        let pointRxRate = 0;
        let pointTxRate = 0;
        
        if (index > 0 && arr[index - 1] && point) {
            const prevPoint = arr[index - 1];
            if (typeof point.time === 'number' && typeof prevPoint.time === 'number') {
                const timeDiff = (point.time - prevPoint.time) / 1000;
                if (timeDiff > 0) {
                    pointRxRate = Math.max(0, (point.rx - prevPoint.rx) / timeDiff);
                    pointTxRate = Math.max(0, (point.tx - prevPoint.tx) / timeDiff);
                }
            }
        }
        
        return {
            time: point.timestamp,
            rx: pointRxRate,
            tx: pointTxRate,
        };
    });

    if (error) {
        return (
            <SectionWidget
                title={<><Icon name="Network" /> {t('network-activity', 'Network Activity')}</>}
                description={t('network-activity.desc', 'Real-time network traffic monitoring')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('error-loading-network', 'Error loading network data')}
                </div>
            </SectionWidget>
        );
    }

    if (isLoading) {
        return (
            <SectionWidget
                title={<><Icon name="Network" /> {t('network-activity', 'Network Activity')}</>}
                description={t('network-activity.desc', 'Real-time network traffic monitoring')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('loading', 'Loading...')}
                </div>
            </SectionWidget>
        );
    }

    return (
        <SectionWidget
            title={<><CommonIcons.Network /> {t('network-activity', 'Network Activity')}</>}
            description={t('network-activity.desc', 'Real-time network traffic monitoring')}
            className="h-full"
        >
            <div className="flex flex-col gap-4 w-full">
                {/* Current Activity Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div className="text-center p-3 rounded bg-green-100">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="ArrowDown" className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="font-semibold text-green-600">
                            {formatBytes(currentRx)}
                        </div>
                        <div className="text-green-600">
                            {t('total-received', 'Total RX')}
                        </div>
                    </div>
                    
                    <div className="text-center p-3 rounded bg-blue-100">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="ArrowUp" className="h-4 w-4 text-blue-600" />
                        </div>
                        <div className="font-semibold text-blue-600">
                            {formatBytes(currentTx)}
                        </div>
                        <div className="text-blue-600">
                            {t('total-transmitted', 'Total TX')}
                        </div>
                    </div>
                    
                    <div className="text-center p-3 rounded bg-green-100">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Activity" className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="font-semibold text-green-600">
                            {formatRate(rxRate)}
                        </div>
                        <div className="text-green-600">
                            {t('rx-rate', 'RX Rate')}
                        </div>
                    </div>
                    
                    <div className="text-center p-3 rounded bg-blue-100">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Activity" className="h-4 w-4 text-blue-600" />
                        </div>
                        <div className="font-semibold text-blue-600">
                            {formatRate(txRate)}
                        </div>
                        <div className="text-blue-600">
                            {t('tx-rate', 'TX Rate')}
                        </div>
                    </div>
                </div>

                {/* Real-time Activity Chart */}
                {chartData.length > 1 && (
                    <div className="w-full">
                        <h4 className="text-sm font-medium mb-3 text-muted-foreground">
                            {t('network-rates-overtime', 'Network Rates Over Time')}
                        </h4>
                        <ChartContainer
                            config={chartConfigWithI18n}
                            className="w-full h-[200px]"
                        >
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart 
                                    data={chartData} 
                                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                >
                                    <XAxis 
                                        dataKey="time"
                                        axisLine={false}
                                        tickLine={false}
                                        className="text-xs fill-muted-foreground"
                                        interval="preserveStartEnd"
                                    />
                                    <YAxis 
                                        axisLine={false}
                                        tickLine={false}
                                        className="text-xs fill-muted-foreground"
                                        tickFormatter={(value: number) => formatRate(value)}
                                    />
                                    <ChartTooltip
                                        content={({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string | number }) => {
                                            if (active && payload && payload.length) {
                                                return (
                                                    <div className="bg-background border rounded p-3 shadow-md">
                                                        <p className="text-sm font-medium mb-2">{label}</p>
                                                        <div className="space-y-1">
                                                            <p className="flex justify-between items-center gap-4">
                                                                <span className="flex items-center gap-2">
                                                                    <div className="w-3 h-3 rounded bg-green-600"></div>
                                                                    RX Rate:
                                                                </span>
                                                                <span className="font-medium">
                                                                    {formatRate(payload[0]?.value as number || 0)}
                                                                </span>
                                                            </p>
                                                            <p className="flex justify-between items-center gap-4">
                                                                <span className="flex items-center gap-2">
                                                                    <div className="w-3 h-3 rounded bg-blue-600"></div>
                                                                    TX Rate:
                                                                </span>
                                                                <span className="font-medium">
                                                                    {formatRate(payload[1]?.value as number || 0)}
                                                                </span>
                                                            </p>
                                                        </div>
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                    <Line 
                                        type="monotone" 
                                        dataKey="rx" 
                                        stroke="var(--color-rx)"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                    <Line 
                                        type="monotone" 
                                        dataKey="tx" 
                                        stroke="var(--color-tx)"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </ChartContainer>
                    </div>
                )}

                {/* Additional Network Stats */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Wifi" className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="font-semibold text-foreground">
                            {networkData?.activeInterfaces || 0}
                        </div>
                        <div className="text-muted-foreground">
                            {t('active-interfaces', 'Active Interfaces')}
                        </div>
                    </div>
                    
                    <div className="text-center p-3 rounded bg-muted/30">
                        <div className="flex items-center justify-center mb-1">
                            <Icon name="Activity" className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="font-semibold text-foreground">
                            {hostMetrics?.activeNodes || 0}
                        </div>
                        <div className="text-muted-foreground">
                            {t('active-nodes', 'Active Nodes')}
                        </div>
                    </div>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span>{t('updating-every-15s', 'Updating every 15 seconds')}</span>
                </div>
            </div>
        </SectionWidget>
    );
};