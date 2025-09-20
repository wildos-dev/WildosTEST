import * as React from "react";
import { useTranslation } from "react-i18next";
import { 
    Card, 
    CardContent, 
    CardHeader, 
    CardTitle,
    Button,
    Textarea,
    Badge,
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
    Input
} from "@wildosvpn/common/components";
import { NodeType, useContainerLogsQuery, useContainerFilesQuery, useContainerRestartMutation } from "@wildosvpn/modules/nodes";
import { Icon } from "@wildosvpn/common/components/ui/icon";

interface ContainerTabProps {
    node: NodeType;
}

export const ContainerTab: React.FC<ContainerTabProps> = ({ node }) => {
    const { t } = useTranslation();
    const [isLogsOpen, setIsLogsOpen] = React.useState(true);
    const [isFilesOpen, setIsFilesOpen] = React.useState(false);
    const [isConfigOpen, setIsConfigOpen] = React.useState(false);
    const [logFilter, setLogFilter] = React.useState("");
    const [currentPath, setCurrentPath] = React.useState("/app");
    
    // Container restart mutation
    const restartMutation = useContainerRestartMutation(node);
    
    const handleContainerRestart = async () => {
        restartMutation.mutate();
    };

    // Fetch container logs and files
    const { data: logs, isLoading: logsLoading } = useContainerLogsQuery(node);
    const { data: files, isLoading: filesLoading } = useContainerFilesQuery(node, currentPath);

    const filteredLogs = logs?.filter((log: any) => 
        logFilter === "" || log.message.toLowerCase().includes(logFilter.toLowerCase())
    ) || [];

    return (
        <div className="space-y-6 p-4">
            {/* Container Actions */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Icon name="RefreshCw" className="h-5 w-5" />
                        {t("labels.container-management")}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex gap-2">
                        <Button 
                            onClick={handleContainerRestart}
                            variant="destructive"
                        >
                            <Icon name="RefreshCw" className="h-4 w-4 mr-2" />
                            {t("buttons.restart-container")}
                        </Button>
                        <Badge variant="outline">
                            {t("labels.status-running")}
                        </Badge>
                    </div>
                </CardContent>
            </Card>

            {/* Real-time Logs Viewer */}
            <Card>
                <Collapsible open={isLogsOpen} onOpenChange={setIsLogsOpen}>
                    <CardHeader>
                        <CollapsibleTrigger asChild>
                            <div className="flex items-center justify-between cursor-pointer">
                                <CardTitle className="flex items-center gap-2">
                                    <Icon name="FileText" className="h-5 w-5" />
                                    {t("labels.container-logs")} ({filteredLogs.length})
                                </CardTitle>
                                {isLogsOpen ? (
                                    <Icon name="ChevronUp" className="h-4 w-4" />
                                ) : (
                                    <Icon name="ChevronDown" className="h-4 w-4" />
                                )}
                            </div>
                        </CollapsibleTrigger>
                    </CardHeader>
                    <CollapsibleContent>
                        <CardContent>
                            {/* Log Controls */}
                            <div className="flex gap-2 mb-4">
                                <div className="flex-1">
                                    <Input
                                        placeholder={t("placeholders.filter-logs")}
                                        value={logFilter}
                                        onChange={(e) => setLogFilter(e.target.value)}
                                        className="w-full"
                                    />
                                </div>
                                <Button variant="outline" size="sm">
                                    <Icon name="Download" className="h-4 w-4 mr-1" />
                                    {t("buttons.export")}
                                </Button>
                                <Button variant="outline" size="sm">
                                    <Icon name="Filter" className="h-4 w-4 mr-1" />
                                    {t("buttons.filter")}
                                </Button>
                            </div>

                            {/* Logs Display */}
                            <div className="bg-black text-green-400 p-4 rounded font-mono text-xs max-h-96 overflow-y-auto">
                                {logsLoading ? (
                                    <div>{t("labels.loading-logs")}</div>
                                ) : filteredLogs.length === 0 ? (
                                    <div>{t("labels.no-logs-available")}</div>
                                ) : (
                                    <div>
                                        {filteredLogs.map((log: any, index: number) => (
                                            <div key={index} className="mb-1">
                                                <span className="text-gray-400">[{log.timestamp}]</span>
                                                <span className={`ml-2 ${
                                                    log.level === 'ERROR' ? 'text-red-400' : 
                                                    log.level === 'WARN' ? 'text-yellow-400' : 
                                                    'text-green-400'
                                                }`}>
                                                    {log.message}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </CollapsibleContent>
                </Collapsible>
            </Card>

            {/* File Explorer */}
            <Card>
                <Collapsible open={isFilesOpen} onOpenChange={setIsFilesOpen}>
                    <CardHeader>
                        <CollapsibleTrigger asChild>
                            <div className="flex items-center justify-between cursor-pointer">
                                <CardTitle className="flex items-center gap-2">
                                    <Icon name="Folder" className="h-5 w-5" />
                                    {t("labels.file-explorer")} ({currentPath})
                                </CardTitle>
                                {isFilesOpen ? (
                                    <Icon name="ChevronUp" className="h-4 w-4" />
                                ) : (
                                    <Icon name="ChevronDown" className="h-4 w-4" />
                                )}
                            </div>
                        </CollapsibleTrigger>
                    </CardHeader>
                    <CollapsibleContent>
                        <CardContent>
                            {/* Path Navigation */}
                            <div className="flex items-center gap-2 mb-4">
                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={() => setCurrentPath("/app")}
                                >
                                    /app
                                </Button>
                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={() => setCurrentPath("/app/config")}
                                >
                                    config
                                </Button>
                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={() => setCurrentPath("/app/logs")}
                                >
                                    logs
                                </Button>
                            </div>

                            {/* Files List */}
                            <div className="border rounded max-h-64 overflow-y-auto">
                                {filesLoading ? (
                                    <div className="p-4">Loading files...</div>
                                ) : files?.length === 0 ? (
                                    <div className="p-4 text-muted-foreground">No files found</div>
                                ) : (
                                    <div>
                                        {files?.map((file: any, index: number) => (
                                            <div 
                                                key={index} 
                                                className="flex items-center justify-between p-3 border-b hover:bg-gray-50 cursor-pointer"
                                                onClick={() => {
                                                    if (file.type === 'directory') {
                                                        setCurrentPath(`${currentPath}/${file.name}`.replace('//', '/'));
                                                    }
                                                }}
                                            >
                                                <div className="flex items-center gap-2">
                                                    {file.type === 'directory' ? (
                                                        <Icon name="Folder" className="h-4 w-4 text-blue-500" />
                                                    ) : (
                                                        <Icon name="FileText" className="h-4 w-4 text-gray-500" />
                                                    )}
                                                    <span>{file.name}</span>
                                                    {file.size && (
                                                        <span className="text-sm text-muted-foreground">
                                                            ({file.size})
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    {file.type === 'file' && (
                                                        <>
                                                            <Button variant="ghost" size="sm">
                                                                <Icon name="Download" className="h-3 w-3" />
                                                            </Button>
                                                            <Button variant="ghost" size="sm">
                                                                <Icon name="Edit" className="h-3 w-3" />
                                                            </Button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        )) || <div className="p-4">No files available</div>}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </CollapsibleContent>
                </Collapsible>
            </Card>

            {/* Configuration Editor */}
            <Card>
                <Collapsible open={isConfigOpen} onOpenChange={setIsConfigOpen}>
                    <CardHeader>
                        <CollapsibleTrigger asChild>
                            <div className="flex items-center justify-between cursor-pointer">
                                <CardTitle className="flex items-center gap-2">
                                    <Icon name="Settings" className="h-5 w-5" />
                                    {t("labels.configuration-editor")}
                                </CardTitle>
                                {isConfigOpen ? (
                                    <Icon name="ChevronUp" className="h-4 w-4" />
                                ) : (
                                    <Icon name="ChevronDown" className="h-4 w-4" />
                                )}
                            </div>
                        </CollapsibleTrigger>
                    </CardHeader>
                    <CollapsibleContent>
                        <CardContent>
                            <div className="space-y-4">
                                {/* Config File Selector */}
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm">
                                        app.conf
                                    </Button>
                                    <Button variant="outline" size="sm">
                                        settings.json
                                    </Button>
                                    <Button variant="outline" size="sm">
                                        docker.env
                                    </Button>
                                </div>

                                {/* Config Editor */}
                                <div>
                                    <Textarea
                                        placeholder={t("placeholders.select-config")}
                                        className="font-mono text-sm min-h-48"
                                        readOnly
                                    />
                                </div>

                                {/* Editor Actions */}
                                <div className="flex gap-2">
                                    <Button variant="default">
                                        Save Changes
                                    </Button>
                                    <Button variant="outline">
                                        Reset
                                    </Button>
                                    <Button variant="outline">
                                        Validate
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </CollapsibleContent>
                </Collapsible>
            </Card>
        </div>
    );
};