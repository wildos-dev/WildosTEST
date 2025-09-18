import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
    Separator,
} from '@wildosvpn/common/components';
import * as React from 'react';

export interface SectionWidgetProps {
    title: any;
    description: any;
    content?: any;
    footer?: any;
    options?: any;
    className?: string;
    titleClassName?: string;
    descriptionClassName?: string;
}

export const SectionWidget: React.FC<SectionWidgetProps & React.PropsWithChildren> = ({
    options, footer, content, children, title, description, className, titleClassName, descriptionClassName
}) => {
    return (
        <Card className={className}>
            <CardHeader className="flex flex-col items-stretch space-y-0 border-b p-0 sm:flex-row">
                <div className="flex flex-1 flex-col justify-center gap-1 px-4 py-4 sm:px-6 sm:py-6">
                    <CardTitle className={`flex flex-row justify-start items-center gap-3 ${titleClassName || 'text-lg sm:text-xl'}`}>
                        {title}
                    </CardTitle>
                    <CardDescription className={descriptionClassName || 'text-sm sm:text-base'}>
                        {description}
                    </CardDescription>
                </div>
                {options &&
                    <div className="flex items-center flex-col justify-center gap-1 px-6 py-5 sm:py-6">
                        {options}
                    </div>
                }
            </CardHeader>
            <Separator />
            <CardContent className="p-4 sm:p-6 flex justify-center">
                {content || children}
            </CardContent>
            {footer && <CardFooter className="flex w-full justify-center"> {footer} </CardFooter>}
        </Card>
    )
}
