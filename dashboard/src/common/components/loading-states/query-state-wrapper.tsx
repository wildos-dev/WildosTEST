import * as React from 'react';
import { Icon } from '@wildosvpn/common/components';
import { Button } from '@wildosvpn/common/components/ui';
import { useTranslation } from 'react-i18next';
import { Skeleton, CardSkeleton } from './skeleton-loader';

interface QueryStateWrapperProps {
  isLoading: boolean;
  isFetching?: boolean;
  isPending?: boolean;
  error?: Error | null;
  data?: any;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onRetry?: () => void;
  loadingComponent?: React.ReactNode;
  backgroundRefetchComponent?: React.ReactNode;
  emptyMessage?: string;
  errorMessage?: string;
  showBackgroundIndicator?: boolean;
}

export const QueryStateWrapper: React.FC<QueryStateWrapperProps> = ({
  isLoading,
  isFetching = false,
  isPending = false,
  error,
  data,
  children,
  fallback,
  onRetry,
  loadingComponent,
  backgroundRefetchComponent,
  emptyMessage,
  errorMessage,
  showBackgroundIndicator = true
}) => {
  const { t } = useTranslation();
  // Loading state
  if (isLoading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>;
    }
    if (fallback) {
      return <>{fallback}</>;
    }
    return <CardSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-6 text-center">
        <Icon name="AlertCircle" className="h-8 w-8 text-destructive mb-3" data-testid="icon-error" />
        <p className="text-slate-400 mb-4" data-testid="text-error">
          {errorMessage || error.message || t('error.loading_data_failed')}
        </p>
        {onRetry && (
          <Button 
            onClick={onRetry} 
            variant="outline" 
            size="sm"
            className="flex items-center gap-2"
            data-testid="button-retry"
          >
            <Icon name="RefreshCw" className="h-4 w-4" />
            {t('error.try_again')}
          </Button>
        )}
      </div>
    );
  }

  // Empty data state
  if (!data || (Array.isArray(data) && data.length === 0)) {
    return (
      <div className="flex flex-col items-center justify-center p-6 text-center">
        <p className="text-slate-400" data-testid="text-empty">{emptyMessage || t('common.no_data')}</p>
      </div>
    );
  }

  // Success state - show children with optional background refetch indicator
  if (showBackgroundIndicator && (isFetching || isPending) && data) {
    return (
      <div className="relative">
        {backgroundRefetchComponent || (
          <div className="absolute top-0 right-0 z-10 p-2" data-testid="indicator-fetching">
            <Icon name="RefreshCw" className="h-4 w-4 animate-spin text-blue-500" />
          </div>
        )}
        {children}
      </div>
    );
  }

  return <>{children}</>;
};

// Specialized wrapper for tables
export const TableQueryWrapper: React.FC<Omit<QueryStateWrapperProps, 'loadingComponent' | 'fallback' | 'backgroundRefetchComponent'> & {
  rows?: number;
  columns?: number;
}> = ({ rows = 5, columns = 4, ...props }) => {
  return (
    <QueryStateWrapper
      {...props}
      loadingComponent={
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="flex gap-4">
              {Array.from({ length: columns }).map((_, j) => (
                <Skeleton key={j} className="h-8 flex-1" />
              ))}
            </div>
          ))}
        </div>
      }
    />
  );
};

// Specialized wrapper for widgets
export const WidgetQueryWrapper: React.FC<Omit<QueryStateWrapperProps, 'loadingComponent' | 'fallback' | 'backgroundRefetchComponent'> & {
  showHeader?: boolean;
  lines?: number;
}> = ({ showHeader = true, lines = 3, ...props }) => {
  return (
    <QueryStateWrapper
      {...props}
      loadingComponent={<CardSkeleton showHeader={showHeader} lines={lines} />}
    />
  );
};