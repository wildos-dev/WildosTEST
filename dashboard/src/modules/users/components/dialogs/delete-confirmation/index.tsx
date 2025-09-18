import * as React from 'react';
import { DeleteConfirmation } from "@wildosvpn/common/components";
import {
    type UserMutationType,
    useUsersDeletionMutation,
} from "@wildosvpn/modules/users";

interface UsersDeleteConfirmationDialogProps {
    onOpenChange: (state: boolean) => void;
    open: boolean;
    entity: UserMutationType;
    onClose: () => void;
}

export const UsersDeleteConfirmationDialog: React.FC<
    UsersDeleteConfirmationDialogProps
> = ({ onOpenChange, open, entity, onClose }) => {
    const deleteMutation = useUsersDeletionMutation();

    React.useEffect(() => {
        if (!open) onClose();
    }, [open, onClose]);

    return (
        <DeleteConfirmation
            open={open}
            onOpenChange={onOpenChange}
            action={() => deleteMutation.mutate(entity)}
        />
    );
};
