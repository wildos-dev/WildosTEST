import { AccordionItem, AccordionTrigger, AccordionContent } from '@wildosvpn/common/components';
import * as React from "react";

interface SettingSectionProps {
    value: string;
    triggerText: string;
}

export const SettingSection: React.FC<SettingSectionProps & React.PropsWithChildren> = ({
    value, triggerText, children
}) => {
    return (
        <AccordionItem
            className="data-[state=open]:bg-muted/40 rounded-lg data-[state=close]:border-muted data-[state=open]:border-muted-foreground border-1 px-3"
            value={value}
        >
            <AccordionTrigger>{triggerText}</AccordionTrigger>
            <AccordionContent>{children}</AccordionContent>
        </AccordionItem>
    );
}
