
import { DeleteConfirmation } from '@wildosvpn/common/components'
import * as React from 'react'
import { ServiceType, useServicesDeletionMutation } from '@wildosvpn/modules/services'

interface ServicesDeleteConfirmationDialogProps {
    onOpenChange: (state: boolean) => void
    open: boolean
    entity: ServiceType
    onClose: () => void;
}

export const ServicesDeleteConfirmationDialog: React.FC<ServicesDeleteConfirmationDialogProps> = ({ onOpenChange, open, entity, onClose }) => {
    const deleteMutation = useServicesDeletionMutation();
    React.useEffect(() => {
        if (!open) onClose();
    }, [open, onClose]);
    return (
        <DeleteConfirmation
            open={open}
            onOpenChange={onOpenChange}
            action={() => deleteMutation.mutate(entity)}
        />
    )
}
