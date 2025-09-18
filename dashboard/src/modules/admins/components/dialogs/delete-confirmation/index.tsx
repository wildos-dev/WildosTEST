import { DeleteConfirmation } from "@wildosvpn/common/components";
import * as React from "react";
import {
    type AdminType,
    useAdminsDeletionMutation,
} from "@wildosvpn/modules/admins";

interface AdminsDeleteConfirmationDialogProps {
    onOpenChange: (state: boolean) => void;
    open: boolean;
    entity: AdminType;
    onClose: () => void;
}

export const AdminsDeleteConfirmationDialog: React.FC<
    AdminsDeleteConfirmationDialogProps
> = ({ onOpenChange, open, entity, onClose }) => {
    const deleteMutation = useAdminsDeletionMutation();

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
