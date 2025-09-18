
export interface PaginatedEntityQueryProps {
    page: number;
    size: number;
}

export type FilteredEntityType = {
    [key: string]: string | undefined;
}

export interface SortedEntityQueryProps {
    sortBy: string
    desc: boolean
}

interface FiltersEntityQueryProps {
    filters: FilteredEntityType;
}

export type UseEntityQueryProps = Partial<FiltersEntityQueryProps> & PaginatedEntityQueryProps & Partial<SortedEntityQueryProps>

export type EntityName = string;
export type ParentEntityName = string;
export type EntityId = number | string | undefined;
export type PrimaryFilter = string;

// QueryKey (5-tuple): [0: entityName, 1: pagination, 2: primaryFilter, 3: sort, 4: filters]
export type QueryKey =
    [EntityName, PaginatedEntityQueryProps, PrimaryFilter, SortedEntityQueryProps, FiltersEntityQueryProps]

// DoubleEntityQueryKey (up to 6-tuple): [0: entityName, 1: entityId, 2: pagination, 3?: primaryFilter, 4?: sort, 5?: filters]
export type DoubleEntityQueryKey =
    [EntityName, EntityId, PaginatedEntityQueryProps, PrimaryFilter?, SortedEntityQueryProps?, FiltersEntityQueryProps?]

// SelectableQueryKey (7-tuple): [0: parentEntityName, 1: parentId, 2: entityName, 3: pagination, 4: primaryFilter, 5: sort, 6: filters]
export type SelectableQueryKey =
    [ParentEntityName, EntityId, EntityName, PaginatedEntityQueryProps, PrimaryFilter, SortedEntityQueryProps, FiltersEntityQueryProps]

// SidebarQueryKey is an alias for SelectableQueryKey to remove structural duplication
export type SidebarQueryKey = SelectableQueryKey;

export interface QueryKeyType<QT> {
    queryKey: QT
}

export type EntityQueryKeyType = QueryKeyType<QueryKey>
export type DoubleEntityQueryKeyType = QueryKeyType<DoubleEntityQueryKey>
export type SelectableEntityQueryKeyType = QueryKeyType<SelectableQueryKey>
export type EntitySidebarQueryKeyType = QueryKeyType<SidebarQueryKey>

interface FetchEntityResult<T> {
    pageCount: number
    entities: T[]
}

export type FetchEntityReturn<T> = Promise<FetchEntityResult<T>>

// Typed helpers for centralized queryKey construction and parsing
export interface ParsedEntityQueryKey {
    entityName: EntityName;
    pagination: PaginatedEntityQueryProps;
    primaryFilter: PrimaryFilter;
    sortInfo: SortedEntityQueryProps;
    filtersInfo: FiltersEntityQueryProps;
}

export interface ParsedSelectableQueryKey {
    parentEntityName: ParentEntityName;
    parentId: EntityId;
    entityName: EntityName;
    pagination: PaginatedEntityQueryProps;
    primaryFilter: PrimaryFilter;
    sortInfo: SortedEntityQueryProps;
    filtersInfo: FiltersEntityQueryProps;
}

// Parse EntityQueryKey (5-tuple) with safe defaults
export function parseEntityQueryKey(queryKey: QueryKey): ParsedEntityQueryKey {
    return {
        entityName: queryKey[0],
        pagination: queryKey.length > 1 && queryKey[1] ? queryKey[1] : { page: 1, size: 10 },
        primaryFilter: queryKey.length > 2 ? queryKey[2] : "",
        sortInfo: queryKey.length > 3 && queryKey[3] ? queryKey[3] : { desc: false, sortBy: "created_at" },
        filtersInfo: queryKey.length > 4 && queryKey[4] ? queryKey[4] : { filters: {} }
    };
}

// Parse SelectableQueryKey (7-tuple) with safe defaults
export function parseSelectableQueryKey(queryKey: SelectableQueryKey): ParsedSelectableQueryKey {
    return {
        parentEntityName: queryKey[0],
        parentId: queryKey[1],
        entityName: queryKey[2],
        pagination: queryKey.length > 3 && queryKey[3] ? queryKey[3] : { page: 1, size: 10 },
        primaryFilter: queryKey.length > 4 ? queryKey[4] : "",
        sortInfo: queryKey.length > 5 && queryKey[5] ? queryKey[5] : { desc: false, sortBy: "created_at" },
        filtersInfo: queryKey.length > 6 && queryKey[6] ? queryKey[6] : { filters: {} }
    };
}

// Build EntityQueryKey consistently
export function buildEntityQueryKey(
    entityName: EntityName,
    pagination: PaginatedEntityQueryProps,
    primaryFilter: PrimaryFilter,
    sortInfo: SortedEntityQueryProps,
    filtersInfo: FiltersEntityQueryProps
): QueryKey {
    return [entityName, pagination, primaryFilter, sortInfo, filtersInfo];
}

// Build SelectableQueryKey consistently  
export function buildSelectableQueryKey(
    parentEntityName: ParentEntityName,
    parentId: EntityId,
    entityName: EntityName,
    pagination: PaginatedEntityQueryProps,
    primaryFilter: PrimaryFilter,
    sortInfo: SortedEntityQueryProps,
    filtersInfo: FiltersEntityQueryProps
): SelectableQueryKey {
    return [parentEntityName, parentId, entityName, pagination, primaryFilter, sortInfo, filtersInfo];
}

// ============================================================================
// NEW ENHANCED UTILITIES FOR MODULE-SPECIFIC QUERY BUILDING
// ============================================================================

/**
 * Module-specific primaryFilter extraction utilities
 * These functions standardize how primaryFilter is extracted from filters for each module
 */

/**
 * Extract primary filter for services module
 * Looks for filters.name or falls back to filters.search
 * @param filters - Filter object containing search criteria
 * @returns The primary filter string for services
 */
export function extractServicesPrimaryFilter(filters: FilteredEntityType): PrimaryFilter {
    return filters?.name || filters?.search || "";
}

/**
 * Extract primary filter for users module
 * Looks for filters.username or falls back to filters.search
 * @param filters - Filter object containing search criteria
 * @returns The primary filter string for users
 */
export function extractUsersPrimaryFilter(filters: FilteredEntityType): PrimaryFilter {
    return filters?.username || filters?.search || "";
}

/**
 * Extract primary filter for nodes module  
 * Looks for filters.name or falls back to filters.search
 * @param filters - Filter object containing search criteria
 * @returns The primary filter string for nodes
 */
export function extractNodesPrimaryFilter(filters: FilteredEntityType): PrimaryFilter {
    return filters?.name || filters?.search || "";
}

/**
 * Extract primary filter for hosts module
 * Looks for filters.remark or falls back to filters.search
 * @param filters - Filter object containing search criteria
 * @returns The primary filter string for hosts
 */
export function extractHostsPrimaryFilter(filters: FilteredEntityType): PrimaryFilter {
    return filters?.remark || filters?.search || "";
}

/**
 * Extract primary filter for admins module
 * Looks for filters.username or falls back to filters.search
 * @param filters - Filter object containing search criteria
 * @returns The primary filter string for admins
 */
export function extractAdminsPrimaryFilter(filters: FilteredEntityType): PrimaryFilter {
    return filters?.username || filters?.search || "";
}

/**
 * High-level module-specific query key builders
 * These functions provide convenient interfaces for building query keys for specific modules
 */

/**
 * Build query key for services module with intelligent primaryFilter extraction
 * @param pagination - Pagination parameters (page, size)
 * @param filters - Filters object (automatically extracts name or search as primaryFilter)
 * @param sortInfo - Sort configuration (optional, defaults to created_at ascending)
 * @returns Complete QueryKey for services
 */
export function buildServicesQueryKey(
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): QueryKey {
    const normalizedFilters = normalizeFiltersWithSearch(filters, "name");
    const primaryFilter = extractServicesPrimaryFilter(normalizedFilters);
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    return buildEntityQueryKey("services", pagination, primaryFilter, sortInfo, filtersInfo);
}

/**
 * Build query key for users module with intelligent primaryFilter extraction
 * @param pagination - Pagination parameters (page, size)
 * @param filters - Filters object (automatically extracts username or search as primaryFilter)
 * @param sortInfo - Sort configuration (optional, defaults to created_at ascending)
 * @returns Complete QueryKey for users
 */
export function buildUsersQueryKey(
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): QueryKey {
    const normalizedFilters = normalizeFiltersWithSearch(filters, "username");
    const primaryFilter = extractUsersPrimaryFilter(normalizedFilters);
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    return buildEntityQueryKey("users", pagination, primaryFilter, sortInfo, filtersInfo);
}

/**
 * Build query key for nodes module with intelligent primaryFilter extraction
 * @param pagination - Pagination parameters (page, size)
 * @param filters - Filters object (automatically extracts name or search as primaryFilter)
 * @param sortInfo - Sort configuration (optional, defaults to created_at ascending)
 * @returns Complete QueryKey for nodes
 */
export function buildNodesQueryKey(
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): QueryKey {
    const normalizedFilters = normalizeFiltersWithSearch(filters, "name");
    const primaryFilter = extractNodesPrimaryFilter(normalizedFilters);
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    return buildEntityQueryKey("nodes", pagination, primaryFilter, sortInfo, filtersInfo);
}

/**
 * Build query key for hosts module with intelligent primaryFilter extraction
 * @param pagination - Pagination parameters (page, size)
 * @param filters - Filters object (automatically extracts remark or search as primaryFilter)
 * @param sortInfo - Sort configuration (optional, defaults to created_at ascending)
 * @returns Complete QueryKey for hosts
 */
export function buildHostsQueryKey(
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): QueryKey {
    const normalizedFilters = normalizeFiltersWithSearch(filters, "remark");
    const primaryFilter = extractHostsPrimaryFilter(normalizedFilters);
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    return buildEntityQueryKey("hosts", pagination, primaryFilter, sortInfo, filtersInfo);
}

/**
 * Build query key for admins module with intelligent primaryFilter extraction
 * @param pagination - Pagination parameters (page, size)
 * @param filters - Filters object (automatically extracts username or search as primaryFilter)
 * @param sortInfo - Sort configuration (optional, defaults to created_at ascending)
 * @returns Complete QueryKey for admins
 */
export function buildAdminsQueryKey(
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): QueryKey {
    const normalizedFilters = normalizeFiltersWithSearch(filters, "username");
    const primaryFilter = extractAdminsPrimaryFilter(normalizedFilters);
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    return buildEntityQueryKey("admins", pagination, primaryFilter, sortInfo, filtersInfo);
}

/**
 * Universal search utilities and backward compatibility helpers
 */

/**
 * Universal primaryFilter extractor that supports filters.search as fallback
 * This function provides a consistent way to extract search terms across all modules
 * @param filters - Filter object containing search criteria
 * @param preferredFields - Array of field names to check before falling back to search
 * @returns The primary filter string
 */
export function extractUniversalPrimaryFilter(
    filters: FilteredEntityType,
    preferredFields: string[] = []
): PrimaryFilter {
    // Try preferred fields first
    for (const field of preferredFields) {
        if (filters?.[field]) {
            return filters[field] || "";
        }
    }
    // Fall back to universal search
    return filters?.search || "";
}

/**
 * Enhanced filter normalization that ensures filters.search is properly handled
 * This function helps migrate existing code to use the universal search pattern
 * @param filters - Original filters object
 * @param searchAlias - Primary field name that should also be copied to filters.search
 * @returns Normalized filters with search alias
 */
export function normalizeFiltersWithSearch(
    filters: FilteredEntityType,
    searchAlias?: string
): FilteredEntityType {
    const normalized = { ...filters };
    
    // If searchAlias is provided and exists, also set it as search
    if (searchAlias && filters?.[searchAlias] && !normalized.search) {
        normalized.search = filters[searchAlias];
    }
    
    // If search exists but searchAlias doesn't, also set searchAlias
    if (searchAlias && filters?.search && !normalized[searchAlias]) {
        normalized[searchAlias] = filters.search;
    }
    
    return normalized;
}

/**
 * Backward compatibility wrapper that automatically applies filter normalization
 * Use this when you need to maintain compatibility with existing code that doesn't use search
 * @param entityName - Name of the entity (services, users, nodes, hosts, admins)
 * @param pagination - Pagination parameters
 * @param filters - Filters object (will be normalized with search support)
 * @param sortInfo - Sort configuration (optional)
 * @returns Complete QueryKey with normalized filters
 */
export function buildCompatibleEntityQueryKey(
    entityName: EntityName,
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): QueryKey {
    // Normalize filters based on entity type
    let normalizedFilters = filters;
    let primaryFilter = "";
    
    switch (entityName) {
        case "services":
            normalizedFilters = normalizeFiltersWithSearch(filters, "name");
            primaryFilter = extractServicesPrimaryFilter(normalizedFilters);
            break;
        case "users":
            normalizedFilters = normalizeFiltersWithSearch(filters, "username");
            primaryFilter = extractUsersPrimaryFilter(normalizedFilters);
            break;
        case "nodes":
            normalizedFilters = normalizeFiltersWithSearch(filters, "name");
            primaryFilter = extractNodesPrimaryFilter(normalizedFilters);
            break;
        case "hosts":
            normalizedFilters = normalizeFiltersWithSearch(filters, "remark");
            primaryFilter = extractHostsPrimaryFilter(normalizedFilters);
            break;
        case "admins":
            normalizedFilters = normalizeFiltersWithSearch(filters, "username");
            primaryFilter = extractAdminsPrimaryFilter(normalizedFilters);
            break;
        default:
            // For unknown entities, use universal search
            primaryFilter = extractUniversalPrimaryFilter(normalizedFilters);
    }
    
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    return buildEntityQueryKey(entityName, pagination, primaryFilter, sortInfo, filtersInfo);
}

/**
 * Type guard to check if an entity name is a known module
 * @param entityName - The entity name to check
 * @returns True if the entity name corresponds to a known module
 */
export function isKnownModuleEntity(entityName: string): entityName is "services" | "users" | "nodes" | "hosts" | "admins" {
    return ["services", "users", "nodes", "hosts", "admins"].includes(entityName);
}

/**
 * Smart query key builder that automatically chooses the best approach
 * This is the recommended function for new code as it handles all edge cases
 * @param entityName - Name of the entity
 * @param pagination - Pagination parameters  
 * @param filters - Filters object (supports both module-specific fields and universal search)
 * @param sortInfo - Sort configuration (optional)
 * @returns Complete QueryKey optimized for the specific module
 */
export function buildSmartQueryKey(
    entityName: EntityName,
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): QueryKey {
    if (isKnownModuleEntity(entityName)) {
        return buildCompatibleEntityQueryKey(entityName, pagination, filters, sortInfo);
    }
    
    // For unknown entities, use the original function with universal search
    const primaryFilter = extractUniversalPrimaryFilter(filters);
    const filtersInfo: FiltersEntityQueryProps = { filters };
    return buildEntityQueryKey(entityName, pagination, primaryFilter, sortInfo, filtersInfo);
}

/**
 * ============================================================================
 * MODULE-SPECIFIC SELECTABLE QUERY KEY BUILDERS FOR INBOUND-SCOPED ENTITIES
 * ============================================================================
 * 
 * These functions handle entities that are scoped to parent entities (e.g., hosts under inbounds)
 * and provide the same filter normalization benefits as the main query key builders
 */

/**
 * Build SelectableQueryKey for hosts module with intelligent primaryFilter extraction and filter normalization
 * Ensures cache consistency between {search:"abc"} and {remark:"abc"} even with inboundId scoping
 * @param parentEntityName - The parent entity name (e.g., "inbounds")
 * @param parentId - The parent entity ID (inboundId)
 * @param pagination - Pagination parameters (page, size)
 * @param filters - Filters object (automatically extracts remark or search as primaryFilter)
 * @param sortInfo - Sort configuration (optional, defaults to created_at ascending)
 * @returns Complete SelectableQueryKey for hosts with proper normalization
 */
export function buildHostsSelectableQueryKey(
    parentEntityName: ParentEntityName,
    parentId: EntityId,
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): SelectableQueryKey {
    const normalizedFilters = normalizeFiltersWithSearch(filters, "remark");
    const primaryFilter = extractHostsPrimaryFilter(normalizedFilters);
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    
    return buildSelectableQueryKey(
        parentEntityName,
        parentId,
        "hosts",
        pagination,
        primaryFilter,
        sortInfo,
        filtersInfo
    );
}

/**
 * Build SelectableQueryKey for users module when scoped to services with proper normalization
 * @param parentEntityName - The parent entity name (e.g., "services")
 * @param parentId - The parent entity ID (serviceId)
 * @param pagination - Pagination parameters (page, size)
 * @param filters - Filters object (automatically extracts username or search as primaryFilter)
 * @param sortInfo - Sort configuration (optional, defaults to created_at ascending)
 * @returns Complete SelectableQueryKey for service-scoped users with proper normalization
 */
export function buildServiceUsersSelectableQueryKey(
    parentEntityName: ParentEntityName,
    parentId: EntityId,
    pagination: PaginatedEntityQueryProps,
    filters: FilteredEntityType = {},
    sortInfo: SortedEntityQueryProps = { desc: false, sortBy: "created_at" }
): SelectableQueryKey {
    const normalizedFilters = normalizeFiltersWithSearch(filters, "username");
    const primaryFilter = extractUsersPrimaryFilter(normalizedFilters);
    const filtersInfo: FiltersEntityQueryProps = { filters: normalizedFilters };
    
    return buildSelectableQueryKey(
        parentEntityName,
        parentId,
        "users",
        pagination,
        primaryFilter,
        sortInfo,
        filtersInfo
    );
}
