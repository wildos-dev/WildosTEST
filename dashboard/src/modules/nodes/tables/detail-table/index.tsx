
import * as React from 'react'
import { NodeType, NodesStatus, NodesStatusBadge, useAllBackendsStatsQuery } from '../..'
import { 
    Table, 
    TableBody, 
    TableCell, 
    TableHead, 
    TableRow,
    Badge 
} from '@wildosvpn/common/components'
import { DateTableRow } from '@wildosvpn/common/components/info-table/date-table-row'
import { format as formatByte } from '@chbphone55/pretty-bytes'
import { useTranslation } from 'react-i18next'


interface NodesDetailTableProps {
    node: NodeType
}


export const NodesDetailTable: React.FC<NodesDetailTableProps> = ({ node }) => {
    const { t } = useTranslation()
    
    // Use the same batch API as NodeCard for unified status source
    const backendStatsQuery = useAllBackendsStatsQuery(node, true, 0) // Always enabled, no jitter for modal
    
    return (
        <Table>
            <TableBody>
                <TableRow >
                    <TableHead >
                        {t('name')}
                    </TableHead>
                    <TableCell >
                        {node.name}
                    </TableCell>
                </TableRow>
                <TableRow>
                    <TableHead >
                        {t('address')}
                    </TableHead>
                    <TableCell >
                        {node.address}:{node.port}
                    </TableCell>
                </TableRow>
                <TableRow>
                    <TableHead className="p-5">
                        {t('page.nodes.usage_coefficient')}
                    </TableHead>
                    <TableCell >
                        {node.usage_coefficient}
                    </TableCell>
                </TableRow>
                <TableRow>
                    <TableHead>
                        {t('status')}
                    </TableHead>
                    <TableCell>
                        <NodesStatusBadge status={NodesStatus[node.status]} />
                    </TableCell>
                </TableRow>
                <TableRow>
                    <TableHead>
                        {t('id')}
                    </TableHead>
                    <TableCell>
                        {node.id}
                    </TableCell>
                </TableRow>
                <TableRow>
                    <TableHead>
                        {t('page.nodes.connection_backend')}
                    </TableHead>
                    <TableCell>
                        {node.connection_backend}
                    </TableCell>
                </TableRow>
                {node.xray_version && (
                    <TableRow>
                        <TableHead>
                            {t('page.nodes.xray_version')}
                        </TableHead>
                        <TableCell>
                            {node.xray_version}
                        </TableCell>
                    </TableRow>
                )}
                {node.message && (
                    <TableRow>
                        <TableHead>
                            {t('message')}
                        </TableHead>
                        <TableCell className="max-w-md whitespace-pre-wrap break-words">
                            {node.message}
                        </TableCell>
                    </TableRow>
                )}
                <DateTableRow 
                    label={t('created_at')} 
                    date={node.created_at}
                    withTime
                />
                {node.last_status_change && (
                    <DateTableRow 
                        label={t('page.nodes.last_status_change')} 
                        date={node.last_status_change}
                        withTime
                    />
                )}
                {(node.uplink !== undefined || node.downlink !== undefined) && (
                    <>
                        <TableRow>
                            <TableHead>
                                {t('page.nodes.uplink')}
                            </TableHead>
                            <TableCell>
                                {node.uplink ? formatByte(node.uplink) : '0 B'}
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableHead>
                                {t('page.nodes.downlink')}
                            </TableHead>
                            <TableCell>
                                {node.downlink ? formatByte(node.downlink) : '0 B'}
                            </TableCell>
                        </TableRow>
                    </>
                )}
                {node.cert_created_at && (
                    <DateTableRow 
                        label={t('page.nodes.cert_issued')} 
                        date={node.cert_created_at}
                    />
                )}
                {node.cert_expires_at && (
                    <DateTableRow 
                        label={t('page.nodes.cert_expires')} 
                        date={node.cert_expires_at}
                    />
                )}
                {node.backends && node.backends.length > 0 && (
                    <TableRow>
                        <TableHead>
                            {t('page.nodes.backends')}
                        </TableHead>
                        <TableCell>
                            <div className="flex flex-wrap gap-2">
                                {node.backends.map((backend) => {
                                    // Get live status from batch API (unified with NodeCard)
                                    const backendStats = backendStatsQuery.data?.[backend.name];
                                    const isRunning = backendStats?.running === true;
                                    const isLoading = backendStatsQuery.isLoading;
                                    
                                    return (
                                        <Badge 
                                            key={backend.name}
                                            variant="outline"
                                            className="text-xs"
                                            title={`${t('type')}: ${backend.backend_type}, ${t('version')}: ${backend.version}, ${t('running')}: ${
                                                isLoading ? t('loading') : isRunning ? t('yes') : t('no')
                                            }`}
                                        >
                                            {backend.name} ({backend.backend_type})
                                            {isLoading && <span className="ml-1 text-gray-400">...</span>}
                                            {!isLoading && isRunning && (
                                                <div className="ml-1 w-2 h-2 bg-green-500 rounded-full" />
                                            )}
                                        </Badge>
                                    );
                                })}
                            </div>
                        </TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
    )
}
