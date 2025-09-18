import {
    Card,
    CardTitle,
    CardContent,
    CardDescription,
    Button,
} from "@wildosvpn/common/components"
import * as React from 'react';
import { Icon } from "@wildosvpn/common/components";
import { projectInfo } from "@wildosvpn/common/utils";

interface GithubRepoProps {
    variant?: "full" | "mini"
    stargazers_count: number;
    full_name?: string;
    description?: string;
}

export const GithubRepo: React.FC<GithubRepoProps> = ({ variant = "full", stargazers_count, full_name, description }) => {
    return (
        <Button variant="secondary" className="bg-gray-800 border-0 dark:text-primary text-secondary dark:hover:text-secondary dark:hover:bg-primary hover:bg-secondary hover:text-primary p-2" asChild>
            <Card>
                <a href={projectInfo.github} target="_blank">
                    <CardContent className="hstack size-fit p-0 gap-2 items-center">
                        <Icon name="Github" className="size-6" />
                        {variant === "full" ? (
                            <div className="vstack items-start">
                                <CardTitle className="font-mono text-xs hstack justify-between w-full">
                                    {full_name}
                                    <div className="hstack gap-1 font-bold items-center text-xs">
                                        <Icon name="Star" className="size-3" />
                                        {stargazers_count}
                                    </div>
                                </CardTitle>
                                <CardDescription className="text-xs">
                                    {description}
                                </CardDescription>
                            </div>
                        ) : (
                            <CardDescription className="hstack gap-1 font-bold items-center text-xs">
                                <Icon name="Star" className="size-3" />
                                {stargazers_count}
                            </CardDescription>
                        )}
                    </CardContent>
                </a>
            </Card>
        </Button>
    )
}
