import * as React from 'react'
import { ScrollArea } from '@wildosvpn/common/components/ui/scroll-area';
import { 
    Card, 
    CardContent, 
    CardFooter, 
    CardHeader, 
    CardTitle 
} from '@wildosvpn/common/components/ui/card';
import { cn } from '@wildosvpn/common/utils';

interface PageProps {
    title: JSX.Element | string;
    content?: JSX.Element | string;
    footer?: JSX.Element | string;
}

export const Page: React.FC<PageProps & React.PropsWithChildren & React.HTMLAttributes<HTMLDivElement>> = ({
    footer,
    content,
    children,
    title,
    className
}) => {
    return (
        <ScrollArea className="w-full h-full overflow-auto">
            <div className="flex flex-col justify-center items-center h-full w-full">
                <Card className="shadow-none border-none p-0 w-full h-full">
                    <CardHeader className="border-none sm:flex-row">
                        <CardTitle className="flex flex-row justify-start items-center text-sans">
                            {title}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className={cn("flex w-full max-w-full", className)}>
                        {content || children}
                    </CardContent>
                    {footer && <CardFooter> {footer} </CardFooter>}
                </Card>
            </div>
        </ScrollArea>
    );
}
