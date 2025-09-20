import {
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
} from '@wildosvpn/common/components';
import * as React from 'react';

export interface MiniWidgetProps extends React.PropsWithChildren {
    title: JSX.Element | string;
    content?: JSX.Element | string;
    footer?: JSX.Element | string;
    className?: string;
}

export const MiniWidget: React.FC<MiniWidgetProps> = ({ footer, content, children, title, className }) => {
    return (
        <Card className={className}>
            <CardHeader className="p-4 sm:p-6">
                <CardTitle className="flex flex-row justify-start items-center gap-3 text-lg sm:text-xl">
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="p-4 sm:p-6">
                {content || children}
            </CardContent>
            {footer && <CardFooter className="p-4 sm:p-6"> {footer} </CardFooter>}
        </Card>
    )
}
