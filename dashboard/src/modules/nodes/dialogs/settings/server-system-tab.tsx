import * as React from "react";
import { useTranslation } from "react-i18next";
import { 
    Card, 
    CardContent, 
    CardHeader, 
    CardTitle,
    Button,
    Badge,
    Input,
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogTrigger,
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger
} from "@wildosvpn/common/components";
import { NodeType, useHostSystemMetricsQuery, PeakEventsSection } from "@wildosvpn/modules/nodes";
import { Icon } from "@wildosvpn/common/components/ui/icon";

interface ServerSystemTabProps {
    node: NodeType;
}

export const ServerSystemTab: React.FC<ServerSystemTabProps> = ({ node }) => {
    const { t } = useTranslation();
    const [isPortsOpen, setIsPortsOpen] = React.useState(false);
    const [portInput, setPortInput] = React.useState("");
    const [isPortDialogOpen, setIsPortDialogOpen] = React.useState(false);
    
    // Fetch host system metrics
    const { data: systemMetrics, isLoading } = useHostSystemMetricsQuery(node);
    
    const handlePortAction = async (action: 'open' | 'close', port: number) => {
        try {
            const endpoint = `/nodes/${node.id}/host/ports/${action}`;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ port, protocol: 'tcp' })
            });
            
            if (response.ok) {
                console.log(`Port ${port} ${action}ed successfully`);
                // Trigger refetch of system metrics to update port list
                window.location.reload();
            } else {
                console.error(`Failed to ${action} port ${port}`);
            }
        } catch (error) {
            console.error(`Error ${action}ing port ${port}:`, error);
        }
    };

    const openPorts = systemMetrics?.openPorts || [];
    const criticalPorts = [22, 443, node.port]; // SSH, HTTPS, node port

    return (
        <div className="space-y-6 p-4">
            {/* System Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                {/* CPU Card */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t("labels.cpu-usage")}</CardTitle>
                        <Icon name="Activity" className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? "..." : `${systemMetrics?.cpu?.usage || 0}%`}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {t("labels.load")}: {systemMetrics?.cpu?.loadAverage?.join(", ") || "..."}
                        </p>
                    </CardContent>
                </Card>

                {/* RAM Card */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t("labels.memory-usage")}</CardTitle>
                        <Icon name="Server" className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? "..." : `${systemMetrics?.memory?.usagePercent || 0}%`}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {systemMetrics?.memory?.used || "..."} / {systemMetrics?.memory?.total || "..."}
                        </p>
                    </CardContent>
                </Card>

                {/* Disk Card */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t("labels.disk-usage")}</CardTitle>
                        <Icon name="HardDrive" className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? "..." : `${systemMetrics?.disk?.rootUsagePercent || 0}%`}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {t("labels.root-partition")}
                        </p>
                    </CardContent>
                </Card>

                {/* Uptime Card */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t("labels.uptime")}</CardTitle>
                        <Icon name="Clock" className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? "..." : systemMetrics?.uptime?.formatted || "..."}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {t("labels.system-uptime")}
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Network Interfaces */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Icon name="Network" className="h-5 w-5" />
                        {t("Network Interfaces")}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div>Loading network data...</div>
                    ) : (
                        <div className="space-y-2">
                            {systemMetrics?.network?.interfaces?.map((iface: any, index: number) => (
                                <div key={index} className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-2 bg-gray-50 rounded gap-2 sm:gap-0">
                                    <div>
                                        <span className="font-medium">{iface.name}</span>
                                        <span className="text-sm text-muted-foreground ml-2">{iface.ip}</span>
                                    </div>
                                    <div className="text-sm">
                                        ↓ {iface.rxBytes} / ↑ {iface.txBytes}
                                    </div>
                                </div>
                            )) || <div>No network interfaces found</div>}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Disk Partitions */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Icon name="HardDrive" className="h-5 w-5" />
                        {t("Disk Partitions")}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div>Loading disk data...</div>
                    ) : (
                        <div className="space-y-2">
                            {systemMetrics?.disk?.partitions?.map((partition: any, index: number) => (
                                <div key={index} className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-2 bg-gray-50 rounded gap-2 sm:gap-0">
                                    <div>
                                        <span className="font-medium">{partition.device}</span>
                                        <span className="text-sm text-muted-foreground ml-2">{partition.mountPoint}</span>
                                    </div>
                                    <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                                        <div className="text-sm">
                                            {partition.used} / {partition.total} ({partition.usagePercent}%)
                                        </div>
                                        <div 
                                            className="w-16 h-2 bg-gray-200 rounded"
                                            title={`${partition.usagePercent}% used`}
                                        >
                                            <div 
                                                className="h-full bg-blue-500 rounded"
                                                style={{ width: `${partition.usagePercent}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )) || <div>No disk partitions found</div>}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Port Management - Collapsible */}
            <Card>
                <Collapsible open={isPortsOpen} onOpenChange={setIsPortsOpen}>
                    <CardHeader>
                        <CollapsibleTrigger asChild>
                            <div className="flex items-center justify-between cursor-pointer">
                                <CardTitle className="flex items-center gap-2">
                                    <Icon name="Shield" className="h-5 w-5" />
                                    {t("Port Management")} ({openPorts.length} open)
                                </CardTitle>
                                {isPortsOpen ? (
                                    <Icon name="ChevronUp" className="h-4 w-4" />
                                ) : (
                                    <Icon name="ChevronDown" className="h-4 w-4" />
                                )}
                            </div>
                        </CollapsibleTrigger>
                    </CardHeader>
                    <CollapsibleContent>
                        <CardContent>
                            {/* Port Management Actions */}
                            <div className="flex gap-2 mb-4">
                                <Dialog open={isPortDialogOpen} onOpenChange={setIsPortDialogOpen}>
                                    <DialogTrigger asChild>
                                        <Button variant="outline">
                                            Open Port
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>Open Port</DialogTitle>
                                            <DialogDescription>
                                                Open a TCP port on the server firewall for network access
                                            </DialogDescription>
                                        </DialogHeader>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="text-sm font-medium">Port Number</label>
                                                <Input
                                                    type="number"
                                                    placeholder={t("placeholders.port-number")}
                                                    value={portInput}
                                                    onChange={(e) => setPortInput(e.target.value)}
                                                    min="1"
                                                    max="65535"
                                                />
                                            </div>
                                            <div className="flex gap-2">
                                                <Button 
                                                    onClick={() => {
                                                        handlePortAction('open', parseInt(portInput));
                                                        setIsPortDialogOpen(false);
                                                        setPortInput("");
                                                    }}
                                                    disabled={!portInput || parseInt(portInput) < 1}
                                                >
                                                    Open Port
                                                </Button>
                                                <Button 
                                                    variant="outline"
                                                    onClick={() => setIsPortDialogOpen(false)}
                                                >
                                                    Cancel
                                                </Button>
                                            </div>
                                        </div>
                                    </DialogContent>
                                </Dialog>
                            </div>

                            {/* Open Ports List */}
                            <div className="space-y-2">
                                <h4 className="font-medium">Open Ports:</h4>
                                {openPorts.length === 0 ? (
                                    <div className="text-muted-foreground">No open ports detected</div>
                                ) : (
                                    <div className="flex flex-wrap gap-2">
                                        {openPorts.map((port: any) => {
                                            const isCritical = criticalPorts.includes(port.number);
                                            return (
                                                <div key={port.number} className="flex items-center gap-2">
                                                    <Badge variant={isCritical ? "destructive" : "default"}>
                                                        {port.number}
                                                        {isCritical && (
                                                            <Icon name="ShieldCheck" className="h-3 w-3 ml-1" />
                                                        )}
                                                    </Badge>
                                                    {!isCritical && (
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() => handlePortAction('close', port.number)}
                                                        >
                                                            Close
                                                        </Button>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>

                            {/* Critical Ports Warning */}
                            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                                <div className="flex items-center gap-2 text-yellow-800">
                                    <Icon name="ShieldCheck" className="h-4 w-4" />
                                    <span className="text-sm font-medium">Protected Ports</span>
                                </div>
                                <p className="text-sm text-yellow-700 mt-1">
                                    Ports {criticalPorts.join(", ")} are protected and cannot be closed (SSH, HTTPS, Node port)
                                </p>
                            </div>
                        </CardContent>
                    </CollapsibleContent>
                </Collapsible>
            </Card>

            {/* Peak Events Section */}
            <PeakEventsSection node={node} />
        </div>
    );
};