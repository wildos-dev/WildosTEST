
import {
    AlertDialog,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle
} from '@wildosvpn/common/components'
import * as React from 'react'
import { useTranslation } from 'react-i18next'

interface InboundNotSelectedAlertDialogProps {
    open: boolean;
    onOpenChange: (s: boolean) => void;
}

export const InboundNotSelectedAlertDialog: React.FC<InboundNotSelectedAlertDialogProps> = (
    { open, onOpenChange }
) => {
    const { t } = useTranslation()
    return (
        <AlertDialog open={open} onOpenChange={onOpenChange}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>
                        {t('page.hosts.no-inbound-selection-alert.title')}
                    </AlertDialogTitle>
                    <AlertDialogDescription>
                        {t('page.hosts.no-inbound-selection-alert.desc')}
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>
                        {t('close')}
                    </AlertDialogCancel>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    )
}
