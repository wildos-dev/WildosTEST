# Standardized API Layer

This directory contains the standardized API layer for the dashboard, ensuring full compatibility with the FastAPI backend.

## Directory Structure

```
src/common/api/
├── index.ts                 # Main exports
├── client.ts               # Typed API client with ofetch
├── query-keys.ts           # Standardized query key patterns
├── mutations.ts            # Mutation helpers and utilities
├── schemas/                # Zod schemas for runtime validation
│   ├── index.ts
│   ├── common.ts           # Common types and utilities
│   ├── user.ts             # User-related schemas
│   ├── admin.ts            # Admin-related schemas
│   ├── node.ts             # Node-related schemas
│   ├── service.ts          # Service-related schemas
│   ├── inbound.ts          # Inbound-related schemas
│   ├── system.ts           # System-related schemas
│   └── subscription.ts     # Subscription-related schemas
└── hooks/                  # Standardized React Query hooks
    ├── index.ts
    ├── use-users.ts        # User API hooks
    ├── use-admins.ts       # Admin API hooks
    ├── use-nodes.ts        # Node API hooks
    ├── use-services.ts     # Service API hooks
    ├── use-inbounds.ts     # Inbound API hooks
    └── use-system.ts       # System API hooks
```

## Key Features

### 1. Type Safety
- Full TypeScript support with Zod runtime validation
- Compile-time and runtime type checking
- Automatic type inference for all API responses

### 2. Standardized Query Keys
- Hierarchical query key structure for efficient cache invalidation
- Consistent patterns across all entities
- Automatic cache management for related queries

### 3. Error Handling
- Unified error handling with custom `ApiError` class
- Automatic 401 handling with logout
- User-friendly error messages
- Proper retry logic for transient failures

### 4. Performance Optimizations
- Intelligent caching with appropriate stale times
- Background refetching for fresh data
- Optimistic updates where appropriate
- Efficient cache invalidation strategies

## Usage Examples

### Basic Query Usage
```typescript
import { useUsersQuery, useUserQuery } from '@wildosvpn/common/api';

function UsersList() {
  const { data, isLoading, error } = useUsersQuery({
    pagination: { page: 1, size: 10 },
    sorting: { order_by: 'created_at', descending: true },
    filters: { enabled: true }
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data?.items.map(user => (
        <UserCard key={user.username} user={user} />
      ))}
    </div>
  );
}
```

### Mutation Usage
```typescript
import { useCreateUserMutation } from '@wildosvpn/common/api';

function CreateUserForm() {
  const createUser = useCreateUserMutation();

  const handleSubmit = (userData) => {
    createUser.mutate(userData, {
      onSuccess: (newUser) => {
        console.log('User created:', newUser);
        // Cache is automatically invalidated
      }
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button 
        type="submit" 
        disabled={createUser.isPending}
      >
        {createUser.isPending ? 'Creating...' : 'Create User'}
      </button>
    </form>
  );
}
```

### Direct API Usage
```typescript
import { api, UserSchema } from '@wildosvpn/common/api';

// With validation
const user = await api.get('users/john', UserSchema);

// Without validation (for custom handling)
const response = await api.get('users/john', UserSchema, { 
  validateResponse: false 
});
```

## Migration from Legacy API

### Before (Legacy)
```typescript
import { fetch } from '@wildosvpn/common/utils';

const result = await fetch('users', {
  query: { page: 1, size: 10 }
});
```

### After (Standardized)
```typescript
import { useUsersQuery } from '@wildosvpn/common/api';

const { data } = useUsersQuery({
  pagination: { page: 1, size: 10 }
});
```

## Benefits

1. **Type Safety**: All API calls are fully typed with runtime validation
2. **Consistency**: Unified patterns across all API endpoints
3. **Performance**: Optimized caching and query invalidation
4. **Error Handling**: Robust error handling with user-friendly messages
5. **Maintainability**: Centralized API logic that's easy to update
6. **Developer Experience**: Excellent IntelliSense and debugging support

## Backend Compatibility

This API layer is designed to be fully compatible with the FastAPI backend:

- All schemas match FastAPI Pydantic models
- Query parameters follow FastAPI conventions
- Error responses are properly typed
- Pagination follows fastapi-pagination patterns
- All endpoints are documented and type-safe