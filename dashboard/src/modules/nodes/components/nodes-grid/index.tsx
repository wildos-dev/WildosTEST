import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useDebounce } from 'use-debounce';
import { useQueryClient } from '@tanstack/react-query';
import {
    Input,
    Button,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    Loading,
    Checkbox
} from '@wildosvpn/common/components';
import { 
    NodeType, 
    NodeCard,
    NodesStatus,
    useNodesQuery
} from '@wildosvpn/modules/nodes';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { z } from 'zod';
import { nodesSearchSchema } from '../../../../routes/_dashboard/nodes';

export const NodesGrid: React.FC = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const search = useSearch({ from: '/_dashboard/nodes' });
    const queryClient = useQueryClient();
    
    // Get values from URL search params (defaults handled by Zod schema)
    const searchQuery = search.q ?? '';
    const statusFilter = search.status;
    const showDisabled = search.showDisabled;
    const page = search.page;
    const pageSize = 12;
    
    // Local search state for immediate UI updates
    const [localSearchQuery, setLocalSearchQuery] = React.useState(searchQuery);
    
    // Debounced search query to avoid excessive API calls
    const [debouncedSearchQuery] = useDebounce(localSearchQuery, 350);
    
    // Update search params when debounced value changes
    React.useEffect(() => {
        if (debouncedSearchQuery !== searchQuery) {
            updateSearchParams({ 
                q: debouncedSearchQuery, 
                page: undefined // Reset page when search changes
            });
        }
    }, [debouncedSearchQuery]);
    
    // Sync local state when URL search changes (e.g., back/forward navigation)
    React.useEffect(() => {
        setLocalSearchQuery(searchQuery);
    }, [searchQuery]);

    const { data, isLoading, error } = useNodesQuery({
        page,
        size: pageSize,
        filters: {
            ...(searchQuery && { name: searchQuery }),
            ...(statusFilter !== 'all' && { status: statusFilter }),
            ...(showDisabled && { showDisabled: 'true' })
        }
    });

    const nodes = data?.entities || [];
    const totalPages = data?.pageCount || 0;

    // Handlers for updating search params
    type NodesSearch = z.infer<typeof nodesSearchSchema>;
    const updateSearchParams = (updates: Partial<NodesSearch>) => {
        // Build complete search object with current values and updates, handling undefined
        const newSearch: NodesSearch = {
            q: updates.hasOwnProperty('q') ? updates.q : search.q,
            status: updates.hasOwnProperty('status') ? (updates.status ?? 'all') : search.status,
            page: updates.hasOwnProperty('page') ? (updates.page ?? 1) : search.page,
            showDisabled: updates.hasOwnProperty('showDisabled') ? (updates.showDisabled ?? false) : search.showDisabled,
        };
        
        // Convert to partial for URL (remove default values) - cast as any to bypass type check
        const urlSearch: any = {};
        if (newSearch.q) urlSearch.q = newSearch.q;
        if (newSearch.status !== 'all') urlSearch.status = newSearch.status;
        if (newSearch.page !== 1) urlSearch.page = newSearch.page;
        if (newSearch.showDisabled !== false) urlSearch.showDisabled = newSearch.showDisabled;
        
        navigate({ to: '/nodes', search: urlSearch, replace: true });
    };

    const handleSearchQueryChange = (value: string) => {
        setLocalSearchQuery(value);
    };
    
    const handleRetryClick = () => {
        // Use proper refetch instead of window.location.reload
        queryClient.invalidateQueries({ 
            queryKey: ['nodes'], 
            exact: false 
        });
    };

    const handleStatusFilterChange = (value: string) => {
        updateSearchParams({ 
            status: value as 'all'|'healthy'|'unhealthy'|'disabled', 
            page: undefined // Reset page when filter changes
        });
    };

    const handlePageChange = (newPage: number) => {
        updateSearchParams({ page: newPage });
    };

    const handleShowDisabledChange = (checked: boolean) => {
        updateSearchParams({ 
            showDisabled: checked, 
            page: undefined // Reset page when filter changes
        });
    };

    const handleNodeClick = (node: NodeType) => {
        navigate({
            to: "/nodes/$nodeId",
            params: { nodeId: String(node.id) },
            search: search, // Preserve search params
        });
    };

    const handleEditClick = (node: NodeType) => {
        navigate({
            to: "/nodes/$nodeId/edit",
            params: { nodeId: String(node.id) },
            search: search, // Preserve search params
        });
    };

    const handleDeleteClick = (node: NodeType) => {
        navigate({
            to: "/nodes/$nodeId/delete",
            params: { nodeId: String(node.id) },
            search: search, // Preserve search params
        });
    };

    const handleCreateClick = () => {
        navigate({ 
            to: "/nodes/create",
            search: search, // Preserve search params
        });
    };


    // Server-side filtering is already handled by useNodesQuery
    // No need for additional client-side filtering
    const filteredNodes = nodes;

    if (isLoading) {
        return <Loading />;
    }

    if (error) {
        return (
            <div className="text-center py-12">
                <div className="text-destructive text-lg mb-2">
                    Error loading nodes
                </div>
                <div className="text-muted-foreground mb-4">
                    {error.message || 'Failed to fetch nodes data'}
                </div>
                <Button 
                    onClick={handleRetryClick} 
                    variant="outline"
                    data-testid="button-retry-nodes"
                >
                    Try again
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Filters and Create Button */}
            <div className="flex flex-col gap-4">
                <div className="flex flex-col lg:flex-row gap-4 items-stretch lg:items-center">
                    <div className="flex flex-col sm:flex-row gap-4 flex-1 min-w-0">
                        {/* Search Input */}
                        <div className="relative flex-1 max-w-full sm:max-w-md">
                            <Icon name="Search" className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder={t("placeholders.search-filter")}
                                value={localSearchQuery}
                                onChange={(e) => handleSearchQueryChange(e.target.value)}
                                className="pl-10 w-full"
                                data-testid="input-search-nodes"
                            />
                        </div>

                        {/* Status Filter */}
                        <Select value={statusFilter} onValueChange={handleStatusFilterChange}>
                            <SelectTrigger className="w-full sm:w-48" data-testid="select-status-filter">
                                <SelectValue placeholder={t('status')} />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all" data-testid="select-option-all">All</SelectItem>
                                <SelectItem value={NodesStatus.healthy.label} data-testid="select-option-healthy">
                                    <span className="capitalize">{NodesStatus.healthy.label}</span>
                                </SelectItem>
                                <SelectItem value={NodesStatus.unhealthy.label} data-testid="select-option-unhealthy">
                                    <span className="capitalize">{NodesStatus.unhealthy.label}</span>
                                </SelectItem>
                                <SelectItem value={NodesStatus.disabled.label} data-testid="select-option-disabled">
                                    <span className="capitalize">{NodesStatus.disabled.label}</span>
                                </SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Create Button - Full width on mobile, compact on larger screens */}
                    <Button onClick={handleCreateClick} className="w-full lg:w-auto shrink-0" data-testid="button-create-node">
                        <Icon name="Plus" className="h-4 w-4 mr-2" />
                        {t('create')}
                    </Button>
                </div>

                {/* Show Disabled Nodes Checkbox - Separate row for better mobile UX */}
                <div className="flex items-center space-x-2">
                    <Checkbox
                        id="showDisabled"
                        checked={showDisabled}
                        onCheckedChange={handleShowDisabledChange}
                        data-testid="checkbox-show-disabled"
                    />
                    <label htmlFor="showDisabled" className="text-sm font-medium cursor-pointer">
                        Show disabled nodes
                    </label>
                </div>
            </div>

            {/* Results Count */}
            <div className="text-sm text-muted-foreground" data-testid="text-nodes-count">
                {t('found')} {filteredNodes.length} {t('nodes')}
            </div>

            {/* Nodes Grid */}
            {filteredNodes.length === 0 ? (
                <div className="text-center py-12">
                    <div className="text-muted-foreground text-lg mb-2">
                        {searchQuery || statusFilter !== 'all' || showDisabled
                            ? t('table.no-result-found') 
                            : t('no-nodes-available')
                        }
                    </div>
                    {(!searchQuery && statusFilter === 'all' && !showDisabled) && (
                        <Button onClick={handleCreateClick} variant="outline" data-testid="button-create-first-node">
                            <Icon name="Plus" className="h-4 w-4 mr-2" />
                            {t('create-first-node')}
                        </Button>
                    )}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" data-testid="grid-nodes">
                    {filteredNodes.map((node: NodeType) => (
                        <NodeCard
                            key={node.id}
                            node={node}
                            onClick={handleNodeClick}
                            onEdit={handleEditClick}
                            onDelete={handleDeleteClick}
                            data-testid={`card-node-${node.id}`}
                        />
                    ))}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex justify-center mt-8">
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            onClick={() => handlePageChange(Math.max(1, page - 1))}
                            disabled={page === 1}
                            data-testid="button-previous-page"
                        >
                            Previous
                        </Button>
                        <span className="text-sm text-muted-foreground px-4" data-testid="text-pagination-info">
                            Page {page} / {totalPages}
                        </span>
                        <Button
                            variant="outline"
                            onClick={() => handlePageChange(Math.min(totalPages, page + 1))}
                            disabled={page >= totalPages}
                            data-testid="button-next-page"
                        >
                            Next
                        </Button>
                    </div>
                </div>
            )}

        </div>
    );
};