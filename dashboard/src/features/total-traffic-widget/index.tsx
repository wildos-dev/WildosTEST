import * as React from 'react';
import { useTranslation } from 'react-i18next';
import {
    SectionWidget,
    ChartContainer,
    Awaiting,
    ChartTooltip,
    ChartTooltipContent,
    ChartConfig,
} from "@wildosvpn/common/components";
import { XAxis, BarChart, YAxis, CartesianGrid, Bar } from "recharts"
import { format as formatByte } from '@chbphone55/pretty-bytes';
import { useTotalTrafficQuery } from "./api";
import { UsageGraphSkeleton } from "./components";
import {
    ChartDateInterval,
    SelectDateView,
    useTransformDateUsageData,
    dateXAxisTicks,
    useFromNowInterval
} from "@wildosvpn/libs/stats-charts";


const TotalTrafficsWidget: React.FC = () => {
    const { t } = useTranslation();
    const [timeRange, setTimeRange] = React.useState("1d")
    const { start, end } = useFromNowInterval(timeRange as ChartDateInterval);
    const { data, isPending } = useTotalTrafficQuery({ start, end })
    const chartData = useTransformDateUsageData(data?.usages || []);
    const [totalAmount, totalMetric] = formatByte(data?.total || 0);
    
    const chartConfigWithI18n = {
        traffic: {
            label: t('metrics.traffic'),
            color: "hsl(var(--chart-1))",
        },
    } satisfies ChartConfig

    return (
        <Awaiting
            Component={
                <SectionWidget
                    title={
                        <div className="hstack justify-between w-full">
                            {t("page.home.total-traffics.title")}
                        </div>
                    }
                    description={t("page.home.total-traffics.desc")}
                    options={
                        <div className="vstack justify-end w-full">
                            <span className="text-lg leading-none sm:text-2xl w-full">
                                {totalAmount} {totalMetric}
                            </span>
                            <span className="text-sm flex justify-end  text-muted-foreground w-full">
                                {t('total')}
                            </span>
                        </div>
                    }
                    footer={
                        <SelectDateView timeRange={timeRange} setTimeRange={setTimeRange} />
                    }
                >
                    <ChartContainer
                        config={chartConfigWithI18n}
                        className="mx-auto w-full aspect-[4/3] md:aspect-[16/9]"
                    >
                        <BarChart
                            accessibilityLayer
                            data={chartData}
                            margin={{
                                left: 12,
                                top: 13,
                                right: 12,
                            }}
                        >
                            <CartesianGrid vertical={false} />
                            <YAxis
                                tickLine={false}
                                axisLine={false}
                                tickMargin={8}
                                tickFormatter={(value: number) => {
                                    const [amount, metric] = formatByte(value)
                                    return `${amount} ${metric}`
                                }}
                            />
                            <XAxis
                                dataKey="datetime"
                                tickLine={false}
                                axisLine={false}
                                tickMargin={8}
                                tickFormatter={(value: string | number) => dateXAxisTicks(String(value), timeRange as ChartDateInterval)}
                            />
                            <ChartTooltip
                                content={
                                    <ChartTooltipContent
                                        indicator='line'
                                        labelFormatter={(value: string | number) => {
                                            return new Date(value).toLocaleDateString("en-US", {
                                                month: "short",
                                                day: "numeric",
                                                year: "numeric",
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
                            <Bar dataKey="traffic" fill={`var(--color-traffic)`} />
                        </BarChart>
                    </ChartContainer>
                </SectionWidget>
            }
            Skeleton={<UsageGraphSkeleton />}
            isFetching={isPending}
        />
    );
};

export { TotalTrafficsWidget };
