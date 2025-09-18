import * as React from 'react';
import { cn } from '@wildosvpn/common/utils';
import { Skeleton as UISkeleton } from '@wildosvpn/common/components/ui/skeleton';

interface SkeletonProps {
  className?: string;
}

// Use the existing UI Skeleton component with consistent styling
export const Skeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <UISkeleton
      className={cn(
        'bg-slate-700/50',
        className
      )}
    />
  );
};

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
};

interface CardSkeletonProps {
  showHeader?: boolean;
  showContent?: boolean;
  lines?: number;
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({ 
  showHeader = true, 
  showContent = true, 
  lines = 3 
}) => {
  return (
    <div className="p-4 border rounded-lg bg-slate-800/50 border-slate-700/50">
      {showHeader && (
        <div className="space-y-2 mb-4">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      )}
      
      {showContent && (
        <div className="space-y-2">
          {Array.from({ length: lines }).map((_, i) => (
            <Skeleton 
              key={i} 
              className={`h-3 ${i === lines - 1 ? 'w-2/3' : 'w-full'}`} 
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface ChartSkeletonProps {
  height?: string;
}

export const ChartSkeleton: React.FC<ChartSkeletonProps> = ({ height = 'h-64' }) => {
  return (
    <div className={`${height} flex items-end gap-2 p-4`}>
      {Array.from({ length: 12 }).map((_, i) => (
        <Skeleton 
          key={i} 
          className={`flex-1 ${
            Math.random() > 0.3 ? 'h-full' : 
            Math.random() > 0.5 ? 'h-3/4' : 'h-1/2'
          }`} 
        />
      ))}
    </div>
  );
};