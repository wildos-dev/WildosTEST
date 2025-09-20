import { useTranslation } from "react-i18next";
import { Button } from "@wildosvpn/common/components";
import * as React from 'react';

export const DonationButton: React.FC<{ donationLink: string }> = ({ donationLink }) => {
    const { t } = useTranslation();
    return (
        <Button size="sm" variant="secondary" className="w-fit" asChild>
            <a
                href={donationLink}
                target="_blank"
                rel="noopener noreferrer"
            >
                {t('support-us.donate')}
            </a>
        </Button>
    )
}
