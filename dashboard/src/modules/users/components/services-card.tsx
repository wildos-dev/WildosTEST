import { EntityFieldCard } from '@wildosvpn/common/components';
import { ServiceType } from '@wildosvpn/modules/services';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import * as React from 'react'

interface ServiceCardProps {
    service: ServiceType
}


export const ServiceCard: React.FC<ServiceCardProps> = (
    { service }
) => {
    return (service.user_ids && service.inbound_ids) && (
        <EntityFieldCard
            FirstIcon={(props: any) => <Icon name="User" {...props} />}
            SecondIcon={(props: any) => <Icon name="Server" {...props} />}
            firstAmount={service.user_ids.length}
            secondAmount={service.inbound_ids.length}
            name={service.name}
        />
    )
};
