import * as React from "react";
import { cn } from "@wildosvpn/common/utils";

export const VStack: React.FC<React.PropsWithChildren & React.HTMLAttributes<HTMLDivElement>> = ({
    children,
    className,
    ...props
}) => {
    return (
        <div className={cn("flex flex-col gap-2", className)} {...props}>
            {children}
        </div>
    );
};
