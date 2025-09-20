import * as React from 'react';
import { Pie, PieChart as RechartsPieChart, ResponsiveContainer, Cell, Label } from 'recharts';

export type PieChartDataRecord = {
    symbol: string,
    amount: number,
    color: string
};

export interface PieChartProps {
    data: PieChartDataRecord[];
    width: number;
    height: number;
    total: number;
    label: string;
}

export const PieChart: React.FC<PieChartProps> = ({ data, width, height, total, label }) => {
    const [active, setActive] = React.useState<PieChartDataRecord | null>(null);
    const chartData = data.map(item => ({ 
        name: item.symbol,
        value: item.amount,
        fill: item.color.startsWith('#') ? item.color : `var(--${item.color})`
    }));

    return (
        <ResponsiveContainer width={width} height={height}>
            <RechartsPieChart>
                <Pie
                    data={chartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={Math.min(width, height) / 2 - 20}
                    innerRadius={Math.min(width, height) / 2 - 60}
                    paddingAngle={1}
                    onMouseEnter={(_, index) => setActive(data[index])}
                    onMouseLeave={() => setActive(null)}
                >
                    {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                    <Label
                        content={({ viewBox }) => {
                            if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                                return (
                                    <>
                                        <text
                                            x={viewBox.cx}
                                            y={viewBox.cy ? viewBox.cy - 10 : 0}
                                            textAnchor="middle"
                                            dominantBaseline="middle"
                                            className="fill-primary text-3xl font-bold"
                                        >
                                            {active ? active.amount : total}
                                        </text>
                                        <text
                                            x={viewBox.cx}
                                            y={viewBox.cy ? viewBox.cy + 20 : 0}
                                            textAnchor="middle"
                                            dominantBaseline="middle"
                                            className="fill-muted-foreground text-sm"
                                        >
                                            {label}
                                        </text>
                                    </>
                                );
                            }
                        }}
                    />
                </Pie>
            </RechartsPieChart>
        </ResponsiveContainer>
    );
};
