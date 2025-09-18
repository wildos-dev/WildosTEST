import { cn } from "@wildosvpn/common/utils";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@wildosvpn/common/components";
import { TruncateTextProps } from '../types';

export function TruncateText({
  text,
  maxLength = 50,
  showTooltip = true,
  className,
  tooltipSide = 'top',
}: TruncateTextProps) {
  const isTruncated = text.length > maxLength;
  const displayText = isTruncated ? `${text.slice(0, maxLength)}...` : text;

  const textElement = (
    <span 
      className={cn(
        "inline-block truncate",
        isTruncated && "cursor-help",
        className
      )}
      title={!showTooltip && isTruncated ? text : undefined}
      data-testid="truncate-text"
    >
      {displayText}
    </span>
  );

  if (!isTruncated || !showTooltip) {
    return textElement;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {textElement}
        </TooltipTrigger>
        <TooltipContent side={tooltipSide} className="max-w-xs break-words">
          {text}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}