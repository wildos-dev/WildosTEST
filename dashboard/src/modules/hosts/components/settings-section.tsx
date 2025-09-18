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
            className="data-[state=open]:bg-muted/40 rounded-lg data-[state=close]:border-muted data-[state=open]:border-muted-foreground border-1 p-4 sm:p-6"
            value={value}
        >
            <AccordionTrigger className="text-sm sm:text-base font-medium hover:no-underline py-4 sm:py-2">
                {triggerText}
            </AccordionTrigger>
            <AccordionContent className="pt-4 pb-2">
                {/* Single column layout on mobile */}
                <div className="space-y-4 sm:space-y-6">
                    {children}
                </div>
            </AccordionContent>
        </AccordionItem>
    );
}
