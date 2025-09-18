import * as React from 'react';
import { UsageGraphSkeleton } from "./components";

// Lazy load the entire TotalTrafficsWidget component
const LazyTotalTrafficsWidget = React.lazy(() => import('./index').then(module => ({ default: module.TotalTrafficsWidget })));

export const TotalTrafficsWidgetLazy: React.FC = () => (
    <React.Suspense fallback={<UsageGraphSkeleton />}>
        <LazyTotalTrafficsWidget />
    </React.Suspense>
);