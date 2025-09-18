import { Icon } from "@wildosvpn/common/components";
import { Button, PopoverTrigger, Popover, PopoverContent } from "@wildosvpn/common/components";
import * as React from 'react';
import { cn } from "@wildosvpn/common/utils";
import { useTranslation } from "react-i18next";
import { DonationButton } from "./donation-button";

export interface SupportUsPopoverProps extends React.HTMLAttributes<HTMLDivElement> {
    donationLink: string;
}

export const SupportUsPopover: React.FC<SupportUsPopoverProps> = ({ className, donationLink }) => {
    const { t } = useTranslation();
    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button size="icon" variant="secondary">
                    <Icon name="HeartHandshake" />
                </Button>
            </PopoverTrigger>
            <PopoverContent sideOffset={10} className={cn("p-4 flex flex-col w-80 gap-2 text-muted-foreground text-sm", className)}>
                <div className="flex-row flex items-center justify-between w-full text-primary">
                    <div className="text-medium flex-row flex gap-1">
                        <Icon name="HeartHandshake" /> {t('support-us.title')}
                    </div>
                </div>
                <p>{t('support-us.desc')}</p>
                <DonationButton donationLink={donationLink} />
            </PopoverContent>
        </Popover>
    );
}

