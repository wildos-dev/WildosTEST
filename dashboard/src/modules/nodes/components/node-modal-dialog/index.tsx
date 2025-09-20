import * as React from "react";
import { 
    Dialog,
    DialogContent,
    DialogTitle,
    DialogDescription,
    ScrollArea,
    Button,
    TruncatedText
} from "@wildosvpn/common/components";
import { Icon } from "@wildosvpn/common/components/ui/icon";
import { cn } from "@wildosvpn/common/utils";
import { NodeType } from "@wildosvpn/modules/nodes";
import { useTranslation } from "react-i18next";

export interface NodeModalDialogProps {
    onOpenChange: (state: boolean) => void;
    open: boolean;
    onClose?: () => void;
    node: NodeType;
}

type WindowState = 'normal' | 'maximized' | 'minimized';

export const NodeModalDialog: React.FC<NodeModalDialogProps & React.PropsWithChildren> = ({
    open,
    onOpenChange,
    children,
    onClose = () => null,
    node
}) => {
    const { t } = useTranslation();
    const [windowState, setWindowState] = React.useState<WindowState>('normal');

    const handleClose = React.useCallback(() => {
        onClose();
        onOpenChange(false);
    }, [onClose, onOpenChange]);

    const handleMinimize = React.useCallback(() => {
        setWindowState(prev => prev === 'minimized' ? 'normal' : 'minimized');
    }, []);

    const handleMaximize = React.useCallback(() => {
        setWindowState(prev => prev === 'maximized' ? 'normal' : 'maximized');
    }, []);

    // Different sizing classes based on window state and device
    const getModalClasses = () => {
        const baseClasses = "fixed z-50 bg-background shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0";
        
        if (windowState === 'maximized') {
            return cn(
                baseClasses,
                "inset-4 rounded-lg border overflow-hidden flex flex-col",
                "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
            );
        }
        
        if (windowState === 'minimized') {
            return cn(
                baseClasses,
                "bottom-4 right-4 w-80 h-16 rounded-lg border overflow-hidden",
                "data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom"
            );
        }

        // Normal state - improved responsive sizing with dvh units
        return cn(
            baseClasses,
            // Fixed positioning with proper centering
            "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2",
            // Improved size constraints with dynamic viewport height
            "max-w-screen-lg w-[95vw] sm:w-[90vw] max-h-[90dvh] h-auto overflow-hidden",
            // Flex layout for proper structure
            "flex flex-col",
            // Styling
            "rounded-lg border",
            // Animations
            "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
            "data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]",
            "data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]"
        );
    };

    if (!open) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent 
                className={getModalClasses()}
                hideCloseButton={true}
                disableDefaultPositioning={true}
                onPointerDownOutside={(e) => {
                    // Prevent closing when clicking outside in minimized state
                    if (windowState === 'minimized') {
                        e.preventDefault();
                    }
                }}
            >
                    {/* Dialog Title - Keep accessible for screen readers */}
                    <DialogTitle className="sr-only">
                        Node Settings - {node.name} (ID: {node.id})
                    </DialogTitle>
                    <DialogDescription className="sr-only">
                        Node management dialog for {node.name}. Use this dialog to configure node settings, view information, and manage the node.
                    </DialogDescription>
                    {/* Custom Header - Sticky */}
                    <div className="flex items-center justify-between border-b px-6 py-4 bg-muted/50 shrink-0">
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                            <div className="min-w-0 flex-1 space-y-1">
                                <TruncatedText 
                                    className="text-lg font-semibold text-foreground"
                                    tooltip={true}
                                    tooltipContent={`${t('name')}: ${node.name}`}
                                >
                                    {node.name}
                                </TruncatedText>
                                <TruncatedText 
                                    className="text-sm text-muted-foreground"
                                    tooltip={true}
                                    tooltipContent={`ID: ${node.id}`}
                                >
                                    ID: {node.id}
                                </TruncatedText>
                            </div>
                        </div>
                        
                        {/* Window Controls */}
                        <div className="flex items-center gap-1">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleMinimize}
                                className="h-8 w-8 p-0"
                                title={windowState === 'minimized' ? t('buttons.restore') : t('buttons.minimize')}
                            >
                                {windowState === 'minimized' ? (
                                    <Icon name="Maximize" className="h-4 w-4" />
                                ) : (
                                    <Icon name="Minus" className="h-4 w-4" />
                                )}
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleMaximize}
                                className="h-8 w-8 p-0"
                                title={windowState === 'maximized' ? t('buttons.restore') : t('buttons.maximize')}
                            >
                                {windowState === 'maximized' ? (
                                    <Icon name="Minimize2" className="h-4 w-4" />
                                ) : (
                                    <Icon name="Maximize" className="h-4 w-4" />
                                )}
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleClose}
                                className="h-8 w-8 p-0"
                                title={t('buttons.close')}
                            >
                                <Icon name="X" className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>

                    {/* Content - Scrollable Body */}
                    {windowState !== 'minimized' && (
                        <div className="flex-1 min-h-0 overflow-hidden">
                            <ScrollArea className="h-full">
                                <div className="px-6 py-4">
                                    {children}
                                </div>
                            </ScrollArea>
                        </div>
                    )}

                    {/* Minimized state content */}
                    {windowState === 'minimized' && (
                        <div className="flex items-center px-4 py-2 min-w-0">
                            <TruncatedText 
                                className="text-sm text-muted-foreground"
                                tooltip={true}
                                tooltipContent={`${t('nodes')}: ${node.name} (ID: ${node.id})`}
                            >
                                {t('nodes')}: {node.name}
                            </TruncatedText>
                        </div>
                    )}
            </DialogContent>
        </Dialog>
    );
};