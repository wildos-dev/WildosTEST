import * as React from 'react';
import { cn } from '@wildosvpn/common/utils/cn';

interface SafeChartContainerProps {
    children: React.ReactNode;
    className?: string;
    fallback?: React.ReactNode;
    minWidth?: number;
    minHeight?: number;
}

const DefaultSkeleton = () => (
    <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-4/6"></div>
        </div>
    </div>
);

export const SafeChartContainer: React.FC<SafeChartContainerProps> = ({
    children,
    className,
    fallback = <DefaultSkeleton />,
    minWidth = 100,
    minHeight = 100,
}) => {
    const containerRef = React.useRef<HTMLDivElement>(null);
    const [isReady, setIsReady] = React.useState(false);
    const [dimensions, setDimensions] = React.useState({ width: 0, height: 0 });

    React.useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        let resizeObserver: ResizeObserver | null = null;
        let intersectionObserver: IntersectionObserver | null = null;
        let isVisible = false;

        // Function to check if container is ready for chart rendering
        const checkReadiness = () => {
            const { width, height } = dimensions;
            const ready = isVisible && width >= minWidth && height >= minHeight;
            
            if (ready !== isReady) {
                setIsReady(ready);
            }
        };

        // Intersection Observer to track visibility
        intersectionObserver = new IntersectionObserver(
            (entries) => {
                const [entry] = entries;
                isVisible = entry.isIntersecting && entry.intersectionRatio > 0;
                checkReadiness();
            },
            {
                threshold: 0.1,
                rootMargin: '50px'
            }
        );

        // Resize Observer to track size changes
        resizeObserver = new ResizeObserver((entries) => {
            const [entry] = entries;
            if (entry) {
                const { width, height } = entry.contentRect;
                setDimensions({ width, height });
                
                // Update readiness after size change
                setTimeout(() => {
                    const ready = isVisible && width >= minWidth && height >= minHeight;
                    if (ready !== isReady) {
                        setIsReady(ready);
                    }
                }, 0);
            }
        });

        // Start observing
        intersectionObserver.observe(container);
        resizeObserver.observe(container);

        // Initial size check
        const rect = container.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });

        return () => {
            intersectionObserver?.disconnect();
            resizeObserver?.disconnect();
        };
    }, [dimensions.width, dimensions.height, isReady, minWidth, minHeight]);

    return (
        <div
            ref={containerRef}
            className={cn('w-full h-full min-h-0', className)}
            style={{ minWidth: `${minWidth}px`, minHeight: `${minHeight}px` }}
        >
            {isReady ? children : fallback}
        </div>
    );
};

SafeChartContainer.displayName = 'SafeChartContainer';