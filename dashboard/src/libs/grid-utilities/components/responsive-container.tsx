import { cn } from "@wildosvpn/common/utils";
import { ContainerProps } from '../types';
import { CONTAINER_PADDINGS, CONTAINER_SIZES } from '../constants';

export function ResponsiveContainer({
  size = 'full',
  padding = 'md',
  className,
  children,
}: ContainerProps) {
  return (
    <div 
      className={cn(
        CONTAINER_SIZES[size],
        CONTAINER_PADDINGS[padding],
        className
      )}
      data-testid="responsive-container"
    >
      {children}
    </div>
  );
}