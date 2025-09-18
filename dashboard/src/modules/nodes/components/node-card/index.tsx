import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver';
import { format as formatByte } from '@chbphone55/pretty-bytes';
import { format as formatDate, isValid } from 'date-fns';
import { 
    Card, 
    CardContent, 
    Badge, 
    Button
} from '@wildosvpn/common/components';
import { 
    NodeType, 
    NodesStatus, 
    NodesStatusBadge,
    useNodesUsageQuery,
    useAllBackendsStatsQuery
} from '@wildosvpn/modules/nodes';
import { 
    useFromNowInterval,
    ChartDateInterval 
} from '@wildosvpn/libs/stats-charts';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { cn } from '@wildosvpn/common/utils';

interface NodeCardProps {
    node: NodeType;
    onEdit: (node: NodeType) => void;
    onDelete: (node: NodeType) => void;
    onClick: (node: NodeType) => void;
    className?: string;
}

const getNodeCardColor = (status: string) => {
    switch (status) {
        case NodesStatus.healthy.label:
            return "from-emerald-400 to-teal-600";
        case NodesStatus.unhealthy.label:
            return "from-red-400 to-pink-600";
        case NodesStatus.disabled.label:
            return "from-gray-400 to-slate-600";
        default:
            return "from-blue-400 to-indigo-600";
    }
};

export const NodeCard: React.FC<NodeCardProps> = ({ 
    node, 
    onEdit, 
    onDelete, 
    onClick,
    className 
}) => {
    const { t } = useTranslation();
    const [timeRange] = React.useState("1d");
    const { start, end } = useFromNowInterval(timeRange as ChartDateInterval);
    const { data: usageData, isLoading: usageLoading } = useNodesUsageQuery({ 
        nodeId: node.id, 
        start, 
        end 
    });
    
    // Visibility-aware polling - only poll when card is visible
    const { elementRef, isIntersecting } = useIntersectionObserver({
        threshold: 0.1, // Trigger when 10% of card is visible
        rootMargin: '50px', // Start polling 50px before card becomes visible
    });

    // Generate consistent jitter for this node (based on node ID)
    const jitter = React.useMemo(() => {
        // Generate jitter between -2 to +2 seconds based on node ID
        const seed = node.id * 1234567; // Simple seed
        return (seed % 4000 - 2000) / 1000; // -2 to +2 seconds
    }, [node.id]);

    // Batch API: Get real status for ALL backends in one request
    const backendStatsQuery = useAllBackendsStatsQuery(
        node, 
        isIntersecting, // Only poll when visible
        jitter // Add jitter to spread requests
    );
    
    // Count actually running backends from batch response
    const runningBackendsCount = React.useMemo(() => {
        if (!backendStatsQuery.data) return 0;
        return Object.values(backendStatsQuery.data).filter(backend => 
            backend?.running === true
        ).length;
    }, [backendStatsQuery.data]);

    const total = usageData?.total ?? 0;
    const [totalAmount, totalMetric] = formatByte(total);
    const gradientClass = getNodeCardColor(node.status || 'default');

    const handleCardClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onClick(node);
    };

    const handleEditClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onEdit(node);
    };

    const handleDeleteClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onDelete(node);
    };

    return (
        <Card 
            ref={elementRef}
            className={cn(
                "relative overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300 group",
                className
            )}
            onClick={handleCardClick}
        >
            {/* Gradient background */}
            <div className={cn(
                "absolute inset-0 bg-gradient-to-br opacity-10 group-hover:opacity-15 transition-opacity",
                gradientClass
            )} />
            
            {/* Action buttons */}
            <div className="absolute top-2 right-2 sm:top-3 sm:right-3 flex gap-1 sm:gap-2 opacity-100 sm:opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity z-20">
                <Button
                    variant="secondary"
                    size="touch-sm"
                    onClick={handleEditClick}
                    className="focus-visible:opacity-100 shadow-lg"
                    title={t('page.nodes.edit_node')}
                >
                    <Icon name="Edit" className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
                <Button
                    variant="destructive"
                    size="touch-sm"
                    onClick={handleDeleteClick}
                    className="focus-visible:opacity-100 shadow-lg"
                    title={t('page.nodes.delete_node')}
                >
                    <Icon name="Trash2" className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
            </div>

            <CardContent className="relative p-4 sm:p-6">
                {/* Header with status */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                        <h3 className="text-lg sm:text-xl font-semibold text-foreground mb-2 truncate pr-24 sm:pr-20">
                            {node.name}
                        </h3>
                        {node.status && NodesStatus[node.status] && (
                            <NodesStatusBadge status={NodesStatus[node.status]} />
                        )}
                    </div>
                </div>

                {/* Node ID */}
                <div className="absolute top-2 left-2 sm:top-3 sm:left-3 z-10">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground bg-background/80 backdrop-blur-sm rounded px-2 py-1">
                        <Icon name="Hash" className="h-3 w-3" />
                        <span className="hidden sm:inline">{t('id')}: </span>
                        <span className="sm:hidden">#</span>
                        <span>{node.id}</span>
                    </div>
                </div>

                {/* Node info */}
                <div className="space-y-2 sm:space-y-3 mb-4 sm:mb-6">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Icon name="Globe" className="h-4 w-4 shrink-0" />
                        <span className="truncate">{node.address}:{node.port}</span>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Icon name="Server" className="h-4 w-4" />
                        <span>{t('page.nodes.usage_coefficient')}: {node.usage_coefficient}</span>
                    </div>

                    {/* Display enabled backends: Xray, SingBox, Hysteria */}
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Icon name="Zap" className="h-4 w-4" />
                        <span>
                            {t('page.nodes.backend')}: {(() => {
                                const enabledBackends = [];
                                
                                // Always show Xray (main backend)
                                enabledBackends.push(node.xray_version ? `Xray ${node.xray_version}` : 'Xray');
                                
                                // Check for SingBox backend
                                const singboxBackend = node.backends.find(b => 
                                    b.backend_type === 'singbox' || b.name.toLowerCase().includes('singbox') || b.name.toLowerCase().includes('sing-box')
                                );
                                if (singboxBackend) {
                                    enabledBackends.push(`SingBox ${singboxBackend.version || ''}`);
                                }
                                
                                // Check for Hysteria backend
                                const hysteriaBackend = node.backends.find(b => 
                                    b.backend_type === 'hysteria' || b.backend_type === 'hysteria2' || b.name.toLowerCase().includes('hysteria')
                                );
                                if (hysteriaBackend) {
                                    enabledBackends.push(`Hysteria ${hysteriaBackend.version || ''}`);
                                }
                                
                                return enabledBackends.join(', ');
                            })()}
                        </span>
                    </div>

                    {node.backends.length > 0 && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Icon name="Zap" className="h-4 w-4" />
                            <span>
                                {runningBackendsCount}/{node.backends.length} {t('page.nodes.backends_running')}
                            </span>
                        </div>
                    )}

                    {/* Certificate info */}
                    {node.cert_created_at && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Icon name="Shield" className="h-4 w-4" />
                            <span>
                                {t('page.nodes.cert_issued')}: {isValid(new Date(node.cert_created_at)) 
                                    ? formatDate(new Date(node.cert_created_at), "P")
                                    : t('invalid_date')
                                }
                            </span>
                        </div>
                    )}
                    {node.cert_expires_at && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Icon name="Shield" className="h-4 w-4" />
                            <span>
                                {t('page.nodes.cert_expires')}: {isValid(new Date(node.cert_expires_at)) 
                                    ? formatDate(new Date(node.cert_expires_at), "P")
                                    : t('invalid_date')
                                }
                            </span>
                        </div>
                    )}
                </div>

                {/* Usage stats */}
                <div className="border-t pt-4">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">
                            {t('page.nodes.traffic_usage')}
                        </span>
                        <div className="text-right">
                            <div className="text-lg font-semibold text-foreground">
                                {usageLoading ? '...' : `${totalAmount} ${totalMetric}`}
                            </div>
                            <div className="text-xs text-muted-foreground">
                                {t('total')}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Backends list - simplified for performance */}
                {node.backends.length > 0 && (
                    <div className="border-t pt-3 sm:pt-4 mt-3 sm:mt-4">
                        <div className="flex flex-wrap gap-1 sm:gap-2">
                            {node.backends.slice(0, 3).map((backend) => {
                                // Get status from batch API response
                                const backendStats = backendStatsQuery.data?.[backend.name];
                                const isRunning = backendStats?.running === true;
                                const isLoading = backendStatsQuery.isLoading;
                                
                                return (
                                    <Badge 
                                        key={backend.name}
                                        variant={isLoading ? "outline" : isRunning ? "default" : "outline"}
                                        className="text-xs"
                                        title={`${t('type')}: ${backend.backend_type}, ${t('version')}: ${backend.version}, ${t('status')}: ${
                                            isLoading ? t('loading') : isRunning ? t('running') : t('down')
                                        }`}
                                    >
                                        {backend.name}
                                        {isRunning && (
                                            <div className="ml-1 w-2 h-2 bg-green-500 rounded-full" />
                                        )}
                                    </Badge>
                                );
                            })}
                            {node.backends.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                    +{node.backends.length - 3} {t('more')}
                                </Badge>
                            )}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};