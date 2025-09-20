import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
    AlertCard,
} from "@wildosvpn/common/components";
import * as React from "react";
import { useTranslation } from "react-i18next";
import {
    NodeBackendType,
    NodesDetailTable,
    NodesUsageWidget
} from "@wildosvpn/modules/nodes";
import { NodeModalDialog, type NodeModalDialogProps } from "../../components/node-modal-dialog";
import { NodeBackendSetting } from "./node-backend-setting";
import { ServerSystemTab } from "./server-system-tab";
import { ContainerTab } from "./container-tab";

interface NodesSettingsDialogProps extends NodeModalDialogProps {
}

export const NodesSettingsDialog: React.FC<NodesSettingsDialogProps> = ({
    onOpenChange,
    open,
    node,
    onClose,
}) => {
    const { t } = useTranslation();

    return (
        <NodeModalDialog open={open} onClose={onClose} onOpenChange={onOpenChange} node={node}>
            <Tabs defaultValue="config">
                <TabsList className="w-full grid grid-cols-2 sm:grid-cols-4">
                    <TabsTrigger className="w-full" value="config">{t("config")}</TabsTrigger>
                    <TabsTrigger className="w-full" value="info">{t("info")}</TabsTrigger>
                    <TabsTrigger className="w-full" value="server">{t("server")}</TabsTrigger>
                    <TabsTrigger className="w-full" value="container">{t("container")}</TabsTrigger>
                </TabsList>
                <TabsContent value="config">
                    {node.backends.length === 0 ? (
                        <AlertCard
                            variant="warning"
                            desc={t('page.nodes.settings.no-backend-alert.desc')}
                            title={t('page.nodes.settings.no-backend-alert.title')}
                        />
                    ) : (
                        <Tabs
                            className="my-3 w-full h-full"
                            defaultValue={node.backends[0].name}
                        >
                            <TabsList className="w-full">
                                {node.backends.map((backend: NodeBackendType) => (
                                    <TabsTrigger
                                        className="capitalize w-full"
                                        value={backend.name}
                                        key={backend.name}
                                    >
                                        {backend.name}
                                    </TabsTrigger>
                                ))}
                            </TabsList>
                            {node.backends.map((backend: NodeBackendType) => (
                                <TabsContent
                                    className="w-full"
                                    value={backend.name}
                                    key={backend.name}
                                >
                                    <NodeBackendSetting node={node} backend={backend.name} />
                                </TabsContent>
                            ))}
                        </Tabs>
                    )}
                </TabsContent>
                <TabsContent value="info">
                    <div className="my-4">
                        <h1 className="font-medium font-header">
                            {t("page.nodes.settings.detail")}
                        </h1>
                        <NodesDetailTable node={node} />
                    </div>
                    <NodesUsageWidget node={node} />
                </TabsContent>
                <TabsContent value="server">
                    <ServerSystemTab node={node} />
                </TabsContent>
                <TabsContent value="container">
                    <ContainerTab node={node} />
                </TabsContent>
            </Tabs>
        </NodeModalDialog>
    );
};
