import * as React from 'react';

export interface UseIntersectionObserverOptions extends IntersectionObserverInit {
    freezeOnceVisible?: boolean;
}

export function useIntersectionObserver(
    options: UseIntersectionObserverOptions = {}
) {
    const {
        threshold = 0,
        root = null,
        rootMargin = '0%',
        freezeOnceVisible = false,
    } = options;

    const [entry, setEntry] = React.useState<IntersectionObserverEntry>();
    const elementRef = React.useRef<HTMLDivElement>(null);

    const frozen = entry?.isIntersecting && freezeOnceVisible;

    React.useEffect(() => {
        const node = elementRef?.current; // DOM node
        const hasIOSupport = !!window.IntersectionObserver;

        if (!hasIOSupport || frozen || !node) return;

        const observerParams = { threshold, root, rootMargin };
        const observer = new IntersectionObserver(
            ([entry]) => setEntry(entry),
            observerParams
        );

        observer.observe(node);

        return () => observer.disconnect();
    }, [threshold, root, rootMargin, frozen]);

    const previousY = React.useRef<number>();
    const previousRatio = React.useRef<number>();

    React.useEffect(() => {
        if (!entry || !entry.boundingClientRect) return;

        if (
            previousY.current !== undefined &&
            previousRatio.current !== undefined
        ) {
            if (
                entry.boundingClientRect.y < previousY.current &&
                entry.intersectionRatio < previousRatio.current
            ) {
                // Scrolling down and element is getting less visible
                setEntry((prev) => prev && { ...prev, isScrollingDown: true });
            } else {
                // Scrolling up or element is getting more visible
                setEntry((prev) => prev && { ...prev, isScrollingDown: false });
            }
        }

        previousY.current = entry.boundingClientRect.y;
        previousRatio.current = entry.intersectionRatio;
    }, [entry]);

    return { elementRef, isIntersecting: entry?.isIntersecting ?? false, entry };
}