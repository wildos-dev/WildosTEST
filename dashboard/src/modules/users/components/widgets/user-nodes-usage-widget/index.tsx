import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { useScreenBreakpoint } from "@wildosvpn/common/hooks";
import {
    SectionWidget,
    ChartLegendContent,
    ChartContainer,
    Awaiting,
    ChartLegend,
    ChartTooltip,
    ChartTooltipContent,
} from "@wildosvpn/common/components";
import { Area, AreaChart, CartesianGrid, YAxis, XAxis } from "recharts"
import { UserNodesUsageWidgetProps } from "./types";
import { dateXAxisTicks, useFromNowInterval, SelectDateView, ChartDateInterval } from "@wildosvpn/libs/stats-charts";
import { useChartConfig, useTransformData } from "./hooks";
import { format as formatByte } from '@chbphone55/pretty-bytes';
import { useUserNodeUsagesQuery } from "@wildosvpn/modules/users";
import { UsageGraphSkeleton } from "./skeleton"

export const UserNodesUsageWidget: React.FC<UserNodesUsageWidgetProps> = ({
    user,
}) => {
    const { t, i18n } = useTranslation();
    const isMobile = !useScreenBreakpoint('md');
    const [timeRange, setTimeRange] = React.useState("1d")
    const { start, end } = useFromNowInterval(timeRange as ChartDateInterval);
    const { data, isPending } = useUserNodeUsagesQuery({ username: user.username, start, end })
    const chartData = useTransformData(data);
    const config = useChartConfig(data);
    const [totalAmount, totalMetric] = formatByte(data.total);

    return (
        <Awaiting
            Component={
                <SectionWidget
                    title={<div className="flex flex-col sm:flex-row sm:justify-between w-full gap-2">
                        <span className="text-base sm:text-lg">{t("page.users.settings.nodes-usage.title")}</span>
                        {isMobile && (
                            <div className="text-right">
                                <span className="text-lg font-semibold">
                                    {totalAmount} {totalMetric}
                                </span>
                                <span className="text-sm text-muted-foreground ml-2">
                                    {t("total")}
                                </span>
                            </div>
                        )}
                    </div>}
                    description={!isMobile ? t("page.users.settings.nodes-usage.desc") : undefined}
                    options={
                        !isMobile ? (
                            <div className="flex flex-col justify-end w-full text-right">
                                <span className="text-lg leading-none sm:text-2xl w-full">
                                    {totalAmount} {totalMetric}
                                </span>
                                <span className="text-sm text-muted-foreground w-full">
                                    {t("total")}
                                </span>
                            </div>
                        ) : undefined
                    }
                    footer={
                        <div className="w-full">
                            <SelectDateView 
                                timeRange={timeRange} 
                                setTimeRange={setTimeRange}
                            />
                        </div>
                    }
                    className="h-full"
                >
                    <ChartContainer
                        className={isMobile 
                            ? "mx-auto w-full aspect-[5/4]"
                            : "mx-auto w-full aspect-[4/3]"
                        }
                        config={config}
                    >
                        <AreaChart
                            accessibilityLayer
                            data={chartData}
                            margin={isMobile ? {
                                left: 8,
                                top: 8,
                                right: 8,
                            } : {
                                left: 13,
                                top: 13,
                                right: 12,
                            }}
                        >
                            <CartesianGrid vertical={false} />
                            <YAxis
                                tickLine={false}
                                axisLine={false}
                                tickMargin={isMobile ? 4 : 8}
                                fontSize={isMobile ? 10 : 12}
                                tickFormatter={(value: number) => {
                                    const [amount, metric] = formatByte(value)
                                    return isMobile ? `${amount}${metric}` : `${amount} ${metric}`
                                }}
                            />
                            <XAxis
                                dataKey="datetime"
                                tickLine={false}
                                axisLine={false}
                                tickMargin={isMobile ? 4 : 8}
                                fontSize={isMobile ? 10 : 12}
                                tickFormatter={(value: string | number) => dateXAxisTicks(String(value), timeRange as ChartDateInterval)}
                            />
                            <ChartTooltip
                                cursor={false}
                                content={
                                    <ChartTooltipContent
                                        indicator='line'
                                        labelFormatter={(value: string | number) => {
                                            return new Date(value).toLocaleDateString(i18n.language, {
                                                month: "short",
                                                day: "numeric",
                                                year: isMobile ? "2-digit" : "numeric",
                                                hour: "numeric"
                                            })
                                        }}
                                        valueFormatter={(value: number | string) => {
                                            const [amount, metric] = formatByte(value as number)
                                            return `${amount} ${metric}`
                                        }}
                                    />
                                }
                            />
                            <defs>
                                {data.node_usages.map(node =>
                                    <linearGradient key={node.node_name} id={node.node_name} x1="0" y1="0" x2="0" y2="1">
                                        <stop
                                            offset="5%"
                                            stopColor={config[node.node_name].color}
                                            stopOpacity={0.1}
                                        />
                                        <stop
                                            offset="95%"
                                            stopColor={config[node.node_name].color}
                                            stopOpacity={0.8}
                                        />
                                    </linearGradient>
                                )}
                            </defs>
                            {data.node_usages.map(node =>
                                <Area
                                    dataKey={node.node_name}
                                    key={node.node_name}
                                    type="natural"
                                    fill={config[node.node_name].color}
                                    fillOpacity={0.4}
                                    stackId={node.node_id}
                                    stroke={config[node.node_name].color}
                                />
                            )}
                            <ChartLegend 
                                content={<ChartLegendContent />}
                                wrapperStyle={isMobile ? { fontSize: '10px' } : {}}
                            />
                        </AreaChart>
                    </ChartContainer>
                </SectionWidget>
            }
            Skeleton={<UsageGraphSkeleton />}
            isFetching={isPending}
        />
    );
};
