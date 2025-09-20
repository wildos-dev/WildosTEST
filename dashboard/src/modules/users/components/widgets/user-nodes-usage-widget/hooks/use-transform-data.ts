import { UserNodeUsagesResponse } from "@wildosvpn/modules/users";

export type ChartDataEntry = {
    datetime: string;
    [key: string]: number | string;
};

export type ChartData = ChartDataEntry[];

export function useTransformData(initialData: UserNodeUsagesResponse): ChartData {
    const chartData: ChartData = [];
    const nodeDataMap: { [date: string]: ChartDataEntry } = {};

    if (!initialData?.node_usages) {
        return chartData;
    }

    initialData.node_usages.forEach(node => {
        if (!node?.usages) return;
        
        node.usages.forEach(usageData => {
            if (!Array.isArray(usageData) || usageData.length < 2) return;
            const [timestamp, usage] = usageData;
            const date = new Date(timestamp * 1000);
            const formattedDate = date.toISOString();

            if (!nodeDataMap[formattedDate]) {
                nodeDataMap[formattedDate] = { datetime: formattedDate };
            }
            nodeDataMap[formattedDate][node.node_name] = usage;
        });
    });

    for (const date in nodeDataMap) {
        chartData.push(nodeDataMap[date]);
    }
    return chartData;
}
