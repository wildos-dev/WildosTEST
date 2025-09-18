import { DeleteConfirmation } from '@wildosvpn/common/components'
import * as React from 'react'
import { HostType, useHostsDeletionMutation } from '@wildosvpn/modules/hosts'

interface HostsDeleteConfirmationDialogProps {
    onOpenChange: (state: boolean) => void
    onClose: () => void
    open: boolean
    entity: HostType
}

export const HostsDeleteConfirmationDialog: React.FC<HostsDeleteConfirmationDialogProps> = ({ onOpenChange, open, entity, onClose }) => {
    const deleteMutation = useHostsDeletionMutation();

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
