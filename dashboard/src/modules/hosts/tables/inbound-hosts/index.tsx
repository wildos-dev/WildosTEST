import * as React from 'react';
import {
    HostType,
    fetchHosts
} from '@wildosvpn/modules/hosts';
import { HostCard } from "./host-card";
import { useNavigate } from "@tanstack/react-router";
import {
    useInboundsQuery,
} from '@wildosvpn/modules/inbounds';
import { SidebarEntityTable } from '@wildosvpn/libs/entity-table';
import { columns } from './columns';
import { useDialog } from '@wildosvpn/common/hooks';
import {
    InboundNotSelectedAlertDialog
} from './inbound-not-selected-alert-dialog';
import {
    InboundCardHeader,
    InboundCardContent,
} from "./inbound-sidebar-card";

export const InboundHostsTable = () => {
    const { data } = useInboundsQuery({ page: 1, size: 100 })
    const [selectedInbound, setSelectedInbound] = React.useState<string | undefined>(data?.entities?.[0]?.id !== undefined ? String(data?.entities?.[0]?.id) : undefined)
    const navigate = useNavigate({ from: "/hosts" })
    const [inboundSelectionAlert, setInboundSelectionAlert] = useDialog();

    const onEdit = (entity: HostType) => navigate({ to: "/hosts/$hostId/edit", params: { hostId: String(entity.id) } });
    const onDelete = (entity: HostType) => navigate({ to: "/hosts/$hostId/delete", params: { hostId: String(entity.id) } });
    const onOpen = (entity: HostType) => navigate({ to: "/hosts/$hostId", params: { hostId: String(entity.id) } });
    
    const cardActions = { onEdit, onDelete, onOpen };

    const onCreate = () => {
        if (selectedInbound) {
            navigate({
                to: "/hosts/$inboundId/create",
                params: {
                    inboundId: selectedInbound,
                }
            })
        } else {
            setInboundSelectionAlert(true)
        }
    };

    return (
        <div className="w-full space-y-4 sm:space-y-6">
            <InboundNotSelectedAlertDialog
                open={inboundSelectionAlert}
                onOpenChange={setInboundSelectionAlert}
            />
            
            {/* Mobile-adapted table with responsive controls */}
            <div className="flex flex-col space-y-4">
                <SidebarEntityTable
                    fetchEntity={fetchHosts}
                    entityKey="inbounds"
                    secondaryEntityKey="hosts"
                    sidebarEntities={data?.entities || []}
                    sidebarEntityId={selectedInbound}
                    columnsFn={columns}
                    filteredColumn='remark'
                    setSidebarEntityId={setSelectedInbound}
                    onCreate={onCreate}
                    onOpen={onOpen}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    sidebarCardProps={{
                        header: InboundCardHeader,
                        content: InboundCardContent
                    }}
                    CardComponent={HostCard}
                    cardActions={cardActions}
                />
            </div>
        </div>
    )
}
