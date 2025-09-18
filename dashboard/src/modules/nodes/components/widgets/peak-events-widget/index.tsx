import * as React from 'react';
import { Icon, CommonIcons } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';
import {
    SectionWidget,
    Badge,
    ScrollArea,
} from "@wildosvpn/common/components";
import { useAggregatePeakEventsQuery } from "@wildosvpn/modules/nodes/api/aggregate-metrics.query";
import type { PeakEvent } from "@wildosvpn/modules/nodes/api/peak-events.query";

const getCategoryIcon = (category: string) => {
    switch (category) {
        case 'CPU':
        case 'MEMORY':
            return (props: any) => <Icon name="Activity" {...props} />;
        case 'DISK':
            return (props: any) => <Icon name="Server" {...props} />;
        case 'NETWORK':
            return (props: any) => <Icon name="Activity" {...props} />;
        case 'BACKEND':
            return (props: any) => <Icon name="Server" {...props} />;
        default:
            return (props: any) => <Icon name="AlertTriangle" {...props} />;
    }
};

const getCategoryColor = (category: string) => {
    switch (category) {
        case 'CPU':
            return 'text-blue-600 bg-blue-100';
        case 'MEMORY':
            return 'text-green-600 bg-green-100';
        case 'DISK':
            return 'text-yellow-600 bg-yellow-100';
        case 'NETWORK':
            return 'text-purple-600 bg-purple-100';
        case 'BACKEND':
            return 'text-red-600 bg-red-100';
        default:
            return 'text-gray-600 bg-gray-100';
    }
};

const getLevelColor = (level: string) => {
    switch (level) {
        case 'CRITICAL':
            return 'text-red-600 bg-red-100';
        case 'HIGH':
            return 'text-orange-600 bg-orange-100';
        default:
            return 'text-yellow-600 bg-yellow-100';
    }
};

const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) {
        return 'Just now';
    } else if (diffInMinutes < 60) {
        return `${diffInMinutes}m ago`;
    } else if (diffInMinutes < 1440) {
        return `${Math.floor(diffInMinutes / 60)}h ago`;
    } else {
        return date.toLocaleDateString();
    }
};

interface PeakEventItemProps {
    event: PeakEvent;
}

const PeakEventItem: React.FC<PeakEventItemProps> = ({ event }) => {
    const Icon = getCategoryIcon(event.category);
    const isResolved = event.resolved_at_ms !== undefined;
    
    return (
        <div className={`flex items-start gap-3 p-3 rounded-lg border ${isResolved ? 'opacity-60' : ''}`}>
            <div className={`p-2 rounded-full ${getCategoryColor(event.category)}`}>
                <Icon className="h-4 w-4" />
            </div>
            
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2">
                        <Badge variant="secondary" className={`text-xs ${getCategoryColor(event.category)}`}>
                            {event.category}
                        </Badge>
                        <Badge variant="outline" className={`text-xs ${getLevelColor(event.level)}`}>
                            {event.level}
                        </Badge>
                        {isResolved && (
                            <Badge variant="outline" className="text-xs text-green-600 bg-green-100">
                                RESOLVED
                            </Badge>
                        )}
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Icon name="Clock" className="h-3 w-3" />
                        {formatTimestamp(event.started_at_ms)}
                    </div>
                </div>
                
                <div className="text-sm text-foreground mb-1">
                    <span className="font-medium">Node {event.node_id}</span>
                    <span className="mx-2">•</span>
                    <span>{event.metric}</span>
                </div>
                
                <div className="text-xs text-muted-foreground">
                    Value: <span className="font-medium">{event.value}</span>
                    {event.threshold && (
                        <>
                            <span className="mx-2">•</span>
                            Threshold: <span className="font-medium">{event.threshold}</span>
                        </>
                    )}
                </div>
                
                {event.context_json && Object.keys(event.context_json).length > 0 && (
                    <div className="text-xs text-muted-foreground mt-1">
                        <details className="cursor-pointer">
                            <summary className="hover:text-foreground">Context</summary>
                            <pre className="mt-1 text-xs bg-muted/50 p-2 rounded">
                                {JSON.stringify(event.context_json, null, 2)}
                            </pre>
                        </details>
                    </div>
                )}
            </div>
        </div>
    );
};

export const PeakEventsWidget: React.FC = () => {
    const { t } = useTranslation();
    const { data: events, isLoading, error } = useAggregatePeakEventsQuery(24);

    if (error) {
        return (
            <SectionWidget
                title={<><Icon name="AlertTriangle" /> {t('peak-events', 'Peak Events')}</>}
                description={t('peak-events.desc', 'Critical monitoring events from all nodes')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('error-loading-events', 'Error loading peak events')}
                </div>
            </SectionWidget>
        );
    }

    if (isLoading) {
        return (
            <SectionWidget
                title={<><Icon name="AlertTriangle" /> {t('peak-events', 'Peak Events')}</>}
                description={t('peak-events.desc', 'Critical monitoring events from all nodes')}
                className="h-full"
            >
                <div className="text-center text-muted-foreground p-4">
                    {t('loading', 'Loading...')}
                </div>
            </SectionWidget>
        );
    }

    const activeEvents = events.filter(event => event.resolved_at_ms === undefined);
    const resolvedEvents = events.filter(event => event.resolved_at_ms !== undefined);
    
    // Statistics
    const categoryStats = events.reduce((acc, event) => {
        acc[event.category] = (acc[event.category] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const levelStats = events.reduce((acc, event) => {
        acc[event.level] = (acc[event.level] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    return (
        <SectionWidget
            title={<><CommonIcons.AlertTriangle /> {t('peak-events', 'Peak Events')}</>}
            description={t('peak-events.desc', 'Critical monitoring events from all nodes')}
            className="h-full"
        >
            <div className="flex flex-col gap-4 h-full">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    <div className="text-center p-2 rounded bg-red-100">
                        <div className="font-semibold text-red-600">{activeEvents.length}</div>
                        <div className="text-red-600">{t('active', 'Active')}</div>
                    </div>
                    <div className="text-center p-2 rounded bg-green-100">
                        <div className="font-semibold text-green-600">{resolvedEvents.length}</div>
                        <div className="text-green-600">{t('resolved', 'Resolved')}</div>
                    </div>
                    <div className="text-center p-2 rounded bg-orange-100">
                        <div className="font-semibold text-orange-600">{levelStats.CRITICAL || 0}</div>
                        <div className="text-orange-600">{t('critical', 'Critical')}</div>
                    </div>
                    <div className="text-center p-2 rounded bg-yellow-100">
                        <div className="font-semibold text-yellow-600">{levelStats.HIGH || 0}</div>
                        <div className="text-yellow-600">{t('high', 'High')}</div>
                    </div>
                </div>

                {/* Events List */}
                <div className="flex-1 min-h-0">
                    {events.length === 0 ? (
                        <div className="text-center text-muted-foreground p-8">
                            <Icon name="AlertTriangle" className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">{t('no-peak-events', 'No peak events in the last 24 hours')}</p>
                            <p className="text-xs mt-1">{t('no-peak-events-desc', 'This is good - your system is running smoothly')}</p>
                        </div>
                    ) : (
                        <ScrollArea className="h-[400px]">
                            <div className="space-y-2 pr-4">
                                {events.map((event) => (
                                    <PeakEventItem key={`${event.node_id}-${event.seq}`} event={event} />
                                ))}
                            </div>
                        </ScrollArea>
                    )}
                </div>

                {/* Category Distribution */}
                {Object.keys(categoryStats).length > 0 && (
                    <div className="border-t pt-3">
                        <h4 className="text-xs font-medium mb-2 text-muted-foreground">
                            {t('event-categories', 'Event Categories')}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(categoryStats).map(([category, count]) => (
                                <Badge 
                                    key={category} 
                                    variant="secondary" 
                                    className={`text-xs ${getCategoryColor(category)}`}
                                >
                                    {category}: {count}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </SectionWidget>
    );
};