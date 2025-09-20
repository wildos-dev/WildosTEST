import * as React from 'react';
import { Icon } from "@wildosvpn/common/components/ui/icon";
import {
    Badge,
    Label,
} from "@wildosvpn/common/components";
import {
    type InboundType
} from '@wildosvpn/modules/inbounds';

export const InboundCardHeader: React.FC<{ entity: InboundType }> = ({ entity }) => {
    return (
        <div className="flex items-center">
            <Label className="font-bold capitalize">{entity.tag}</Label>
        </div>
    )
}

export const InboundCardContent: React.FC<{ entity: InboundType }> = ({ entity }) => {
    return (
        <div className="flex justify-between">
            <div className="hstack items-center">
                <Icon name="Box" className="p-1" /> {entity.node.name}
            </div>
            <Badge>
                {entity.protocol}
            </Badge>

        </div>
    )
}
