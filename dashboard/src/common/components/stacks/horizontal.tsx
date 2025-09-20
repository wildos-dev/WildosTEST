import * as React from "react";
import { cn } from "@wildosvpn/common/utils";

export const HStack: React.FC<React.PropsWithChildren & React.HTMLAttributes<HTMLDivElement>> = ({
    children,
    className,
}) => {
    return <div className={cn("flex flex-row gap-2", className)}>{children}</div>;
};
