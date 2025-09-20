import * as React from "react";
import { cn } from "@wildosvpn/common/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

interface TruncatedTextProps {
    children: React.ReactNode;
    className?: string;
    maxLines?: number;
    tooltip?: boolean;
    tooltipContent?: React.ReactNode;
    title?: string;
}

export const TruncatedText: React.FC<TruncatedTextProps> = ({
    children,
    className,
    maxLines = 1,
    tooltip = true,
    tooltipContent,
    title,
    ...props
}) => {
    const textRef = React.useRef<HTMLDivElement>(null);
    const [isTruncated, setIsTruncated] = React.useState(false);

    React.useEffect(() => {
        const element = textRef.current;
        if (!element) return;

        const checkTruncation = () => {
            if (maxLines === 1) {
                setIsTruncated(element.scrollWidth > element.clientWidth);
            } else {
                setIsTruncated(element.scrollHeight > element.clientHeight);
            }
        };

        checkTruncation();

        // Re-check on resize
        const resizeObserver = new ResizeObserver(checkTruncation);
        resizeObserver.observe(element);

        return () => resizeObserver.disconnect();
    }, [children, maxLines]);

    const lineClampMap = {
        1: 'truncate',
        2: 'line-clamp-2',
        3: 'line-clamp-3',
        4: 'line-clamp-4',
        5: 'line-clamp-5',
        6: 'line-clamp-6',
    } as const;

    const textElement = (
        <div
            ref={textRef}
            className={cn(
                "min-w-0 break-words hyphens-auto",
                lineClampMap[maxLines as keyof typeof lineClampMap] || 'truncate',
                className
            )}
            title={title || (typeof children === 'string' ? children : undefined)}
            {...props}
        >
            {children}
        </div>
    );

    // Show tooltip if requested and text is truncated
    if (tooltip && isTruncated) {
        return (
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        {textElement}
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="max-w-xs break-words">
                            {tooltipContent || children}
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        );
    }

    return textElement;
};

TruncatedText.displayName = "TruncatedText";