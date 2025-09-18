
import { DeleteConfirmation } from '@wildosvpn/common/components'
import * as React from 'react'
import { NodeType, useNodesDeletionMutation } from '@wildosvpn/modules/nodes'

interface NodesDeleteConfirmationDialogProps {
    onOpenChange: (state: boolean) => void
    open: boolean
    entity: NodeType
    onClose: () => void
}

export const NodesDeleteConfirmationDialog: React.FC<NodesDeleteConfirmationDialogProps> = (
    { onOpenChange, open, entity, onClose }
) => {
    const deleteMutation = useNodesDeletionMutation();

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
