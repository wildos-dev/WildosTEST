import * as React from "react";
import { useTranslation } from "react-i18next";
import { 
    Card, 
    CardContent, 
    CardHeader, 
    CardTitle,
    Badge,
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import type { NodeType } from "@wildosvpn/modules/nodes";
import { usePeakEventsStream, useRecentPeakEventsQuery, type PeakEvent } from "@wildosvpn/modules/nodes/api/peak-events.query";

interface PeakEventsSectionProps {
    node: NodeType;
}

export const PeakEventsSection: React.FC<PeakEventsSectionProps> = ({ node }) => {
    const { t, i18n } = useTranslation();
    const [isPeakEventsOpen, setIsPeakEventsOpen] = React.useState(false);
    
    // Get real-time and historical peak events
    const { events: realtimePeakEvents, isConnected: peakEventsConnected } = usePeakEventsStream(node);
    const { data: recentPeakEvents = [] } = useRecentPeakEventsQuery(node);
    
    // Combine and deduplicate events (prioritize real-time events)
    const allEvents = [...realtimePeakEvents, ...recentPeakEvents]
        .filter((event, index, arr) => 
            arr.findIndex(e => e.dedupe_key === event.dedupe_key) === index
        )
        .sort((a, b) => b.started_at_ms - a.started_at_ms)
        .slice(0, 20); // Show last 20 events

    const formatTimestamp = (timestamp: number) => {
        return new Date(timestamp).toLocaleString(i18n.language);
    };

    const formatDuration = (startedAt: number, resolvedAt?: number) => {
        if (!resolvedAt) return t("nodes.peak_events.ongoing");
        const duration = Math.round((resolvedAt - startedAt) / 1000 / 60); // minutes
        return duration > 0 ? `${duration} ${t("nodes.peak_events.duration_min")}` : t("nodes.peak_events.duration_less_than_min");
    };

    const getCategoryIcon = (category: PeakEvent['category']) => {
        switch (category) {
            case 'CPU': return <Icon name="TrendingUp" className="h-4 w-4" />;
            case 'MEMORY': return <Icon name="Zap" className="h-4 w-4" />;
            case 'DISK': return <Icon name="AlertTriangle" className="h-4 w-4" />;
            case 'NETWORK': return <Icon name="AlertTriangle" className="h-4 w-4" />;
            case 'BACKEND': return <Icon name="Users" className="h-4 w-4" />;
            default: return <Icon name="AlertTriangle" className="h-4 w-4" />;
        }
    };

    const getCategoryColor = (category: PeakEvent['category'], level: PeakEvent['level']) => {
        const isHigh = level === 'HIGH';
        switch (category) {
            case 'CPU': return isHigh ? 'bg-orange-100 text-orange-800' : 'bg-red-100 text-red-800';
            case 'MEMORY': return isHigh ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800';
            case 'DISK': return isHigh ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800';
            case 'NETWORK': return isHigh ? 'bg-cyan-100 text-cyan-800' : 'bg-indigo-100 text-indigo-800';
            case 'BACKEND': return isHigh ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const formatContextInfo = (context: Record<string, any>) => {
        const info = [];
        if (context.active_users !== undefined) {
            info.push(`${t("nodes.peak_events.users")}: ${context.active_users}`);
        }
        if (context.connection_count !== undefined) {
            info.push(`${t("nodes.peak_events.connections")}: ${context.connection_count}`);
        }
        if (context.backend_status) {
            info.push(`${t("nodes.peak_events.backend")}: ${context.backend_status}`);
        }
        if (context.traffic_rate_mbps !== undefined) {
            info.push(`${t("nodes.peak_events.traffic")}: ${context.traffic_rate_mbps} Mbps`);
        }
        return info.length > 0 ? info.join(', ') : t("nodes.peak_events.no_additional_info");
    };

    const getCategoryDisplayName = (category: PeakEvent['category']) => {
        const categoryKey = category.toLowerCase();
        return t(`nodes.peak_events.categories.${categoryKey}`) || category;
    };

    const activePeaks = allEvents.filter(event => !event.resolved_at_ms);
    const resolvedPeaks = allEvents.filter(event => event.resolved_at_ms);

    return (
        <Card>
            <Collapsible open={isPeakEventsOpen} onOpenChange={setIsPeakEventsOpen}>
                <CardHeader>
                    <CollapsibleTrigger asChild>
                        <div className="flex items-center justify-between cursor-pointer">
                            <CardTitle className="flex items-center gap-2">
                                <Icon name="AlertTriangle" className="h-5 w-5" />
                                {t("nodes.peak_events.title", { count: allEvents.length })}
                                {peakEventsConnected && (
                                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title={t("nodes.peak_events.connected_to_stream")} />
                                )}
                            </CardTitle>
                            {isPeakEventsOpen ? (
                                <Icon name="ChevronUp" className="h-4 w-4" />
                            ) : (
                                <Icon name="ChevronDown" className="h-4 w-4" />
                            )}
                        </div>
                    </CollapsibleTrigger>
                </CardHeader>
                <CollapsibleContent>
                    <CardContent>
                        {allEvents.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Icon name="AlertTriangle" className="h-12 w-12 mx-auto mb-4 opacity-30" />
                                <p>{t("nodes.peak_events.no_events_detected")}</p>
                                <p className="text-sm">{t("nodes.peak_events.system_tracking")}</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {/* Active peaks warning */}
                                {activePeaks.length > 0 && (
                                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                        <div className="flex items-center gap-2 text-red-800 mb-2">
                                            <Icon name="AlertTriangle" className="h-4 w-4" />
                                            <span className="font-medium">{t("nodes.peak_events.active_peaks", { count: activePeaks.length })}</span>
                                        </div>
                                        <div className="space-y-2">
                                            {activePeaks.map((event) => (
                                                <div key={event.dedupe_key} className="text-sm text-red-700">
                                                    <Badge className={getCategoryColor(event.category, event.level)}>
                                                        {getCategoryDisplayName(event.category)}: {event.value}% ({t("nodes.peak_events.threshold")} {event.threshold}%)
                                                    </Badge>
                                                    <span className="ml-2">{t("nodes.peak_events.since")} {formatTimestamp(event.started_at_ms)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                
                                {/* Events history */}
                                <div className="space-y-3">
                                    <h4 className="font-medium flex items-center gap-2">
                                        <Icon name="Clock" className="h-4 w-4" />
                                        {t("nodes.peak_events.event_history")}
                                    </h4>
                                    {resolvedPeaks.map((event) => (
                                        <div key={event.dedupe_key} className="p-3 border rounded-lg bg-gray-50">
                                            <div className="flex items-start justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                    {getCategoryIcon(event.category)}
                                                    <Badge className={getCategoryColor(event.category, event.level)}>
                                                        {getCategoryDisplayName(event.category)}
                                                    </Badge>
                                                    <Badge variant={event.level === 'CRITICAL' ? 'destructive' : 'secondary'}>
                                                        {event.level === 'CRITICAL' ? t("nodes.peak_events.levels.critical") : t("nodes.peak_events.levels.high")}
                                                    </Badge>
                                                </div>
                                                <div className="text-sm text-muted-foreground">
                                                    {formatDuration(event.started_at_ms, event.resolved_at_ms)}
                                                </div>
                                            </div>
                                            
                                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 text-sm">
                                                <div>
                                                    <div className="font-medium">{t("nodes.peak_events.values")}:</div>
                                                    <div>{t("nodes.peak_events.peak_value")}: {event.value}%</div>
                                                    <div>{t("nodes.peak_events.threshold_value")}: {event.threshold}%</div>
                                                    <div>{t("nodes.peak_events.metric")}: {event.metric}</div>
                                                </div>
                                                
                                                <div>
                                                    <div className="font-medium">{t("nodes.peak_events.time")}:</div>
                                                    <div>{t("nodes.peak_events.start")}: {formatTimestamp(event.started_at_ms)}</div>
                                                    {event.resolved_at_ms && (
                                                        <div>{t("nodes.peak_events.end")}: {formatTimestamp(event.resolved_at_ms)}</div>
                                                    )}
                                                </div>
                                            </div>
                                            
                                            {/* Context information */}
                                            <div className="mt-3 pt-3 border-t">
                                                <div className="font-medium text-sm mb-1">{t("nodes.peak_events.diagnostic_context")}:</div>
                                                <div className="text-sm text-muted-foreground">
                                                    {formatContextInfo(event.context_json)}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                
                                {/* Connection status */}
                                <div className="text-xs text-muted-foreground border-t pt-3">
                                    {t("nodes.peak_events.connection_status")}: {peakEventsConnected ? 
                                        <span className="text-green-600">{t("nodes.peak_events.connected_to_event_stream")}</span> : 
                                        <span className="text-orange-600">{t("nodes.peak_events.reconnecting")}</span>
                                    }
                                </div>
                            </div>
                        )}
                    </CardContent>
                </CollapsibleContent>
            </Collapsible>
        </Card>
    );
};