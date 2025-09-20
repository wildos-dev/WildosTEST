import {
    Button,
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@wildosvpn/common/components";
import CopyToClipboard from "react-copy-to-clipboard";
import * as React from "react";
import { useTranslation } from "react-i18next";
import { Icon } from "@wildosvpn/common/components";
import { ElementType } from "react";
import { toast } from "sonner";
import { cn } from "@wildosvpn/common/utils";

interface CopyToClipboardButtonProps {
    text: string;
    disabled?: boolean;
    successMessage: string;
    copyIcon?: ElementType;
    copyLabel?: string;
    errorLabel?: string;
    className?: string;
    tooltipMsg?: string;
}

export const CopyToClipboardButton: React.FC<CopyToClipboardButtonProps> = ({
    text,
    disabled = false,
    successMessage,
    copyIcon,
    copyLabel,
    errorLabel,
    className,
    tooltipMsg,
}) => {
    const { t } = useTranslation();
    const [copied, setCopied] = React.useState(false);
    const [healthy, setHealthy] = React.useState(false);

    React.useEffect(() => {
        if (copied) {
            toast.success(t(successMessage));
            setTimeout(() => {
                setCopied(false);
            }, 1000);
        }
    }, [copied, successMessage, t]);

    React.useEffect(() => {
        setHealthy(text !== "");
    }, [text]);

    const handleClick = () => {
        if (!disabled) {
            setCopied(true);
        }
    };

    const tooltip = tooltipMsg ? tooltipMsg : copyLabel ? copyLabel : undefined;

    const IconComponent = copyIcon || (() => <Icon name="ClipboardCopy" />);
    const iconName = copied ? "CopyCheck" : healthy ? undefined : "CopyX";
    const isWithLabel = successMessage && copyLabel && errorLabel;

    return (
        <Tooltip>
            <CopyToClipboard text={text}>
                <TooltipTrigger asChild>
                    <Button
                        className={cn(className, "p-2 flex flex-row items-center gap-2")}
                        disabled={disabled || !healthy}
                        onClick={handleClick}
                    >
                        {iconName ? <Icon name={iconName} /> : <IconComponent />}
                        {isWithLabel &&
                            t(copied ? successMessage : healthy ? copyLabel : errorLabel)}
                    </Button>
                </TooltipTrigger>
            </CopyToClipboard>
            {tooltip && <TooltipContent>{tooltip}</TooltipContent>}
        </Tooltip>
    );
};
