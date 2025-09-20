import {
    ChartConfig,
} from "@wildosvpn/common/components";
import { UserNodeUsagesResponse } from "@wildosvpn/modules/users";

export const useChartConfig = (nodesUsage: UserNodeUsagesResponse) => {
    const numberOfNodes = nodesUsage.node_usages.length;
    const config: Record<string, any> = {
        views: {
            label: "Page Views",
        }
    }
    // Color palette for charts
    const colorPalette = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', 
        '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6b7280'
    ];
    const colors = Array.from({ length: numberOfNodes }, (_, i) => 
        colorPalette[i % colorPalette.length]
    );
    nodesUsage.node_usages.forEach((node, i) => {
        config[node.node_name] = { label: node.node_name, color: colors[i] };
    })
    return config satisfies ChartConfig;
}
