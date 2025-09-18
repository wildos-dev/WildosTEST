import * as React from 'react';
import { SupportUsVariation } from "./types";
import { Icon } from "@wildosvpn/common/components";
import { Button, Card, CardTitle, CardContent } from "@wildosvpn/common/components";
import { cn } from "@wildosvpn/common/utils";
import { useTranslation } from "react-i18next";

export interface SupportUsCardProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: SupportUsVariation;
    donationLink: string;
    setSupportUsOpen: (state: boolean) => void;
}

export const SupportUsCard: React.FC<SupportUsCardProps> = ({ className, variant, setSupportUsOpen, donationLink }) => {
    const { t } = useTranslation();
    return (
        <Card>
            <CardContent className={cn("p-4 flex flex-col w-fit gap-2 text-muted-foreground text-sm", className)}>
                <CardTitle className="flex-row flex items-center justify-between w-full text-primary">
                    <div className="text-medium flex-row flex gap-1">
                        <Icon name="HeartHandshake" /> {t('support-us.title')}
                    </div>
                    {variant !== "view" && (
                        <Button
                            variant="ghost"
                            className="size-6 p-0 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none text-muted-foreground"
                            onMouseDown={() => setSupportUsOpen(false)}
                        >
                            <Icon name="X" className="size-4" />
                            <span className="sr-only">{t('close')}</span>
                        </Button>
                    )}
                </CardTitle>
                <p>{t('support-us.desc')}</p>
                <Button size="sm" variant="secondary" className="w-fit" asChild>
                    <a
                        href={donationLink}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {t('support-us.donate')}
                    </a>
                </Button>
            </CardContent>
        </Card>
    );
}
