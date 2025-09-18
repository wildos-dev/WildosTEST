import { ElementType } from 'react';
import { Label, Separator } from '@wildosvpn/common/components';
import * as React from 'react'

interface EntityFieldCardProps {
    FirstIcon: ElementType;
    SecondIcon: ElementType;
    firstAmount: number | string;
    secondAmount: number | string;
    name: string;
}


export const EntityCardProperty = ({ Icon, amount }: { Icon: ElementType, amount: number | string }) => (
    <div className="flex flex-row items-center w-full">
        <Icon className="w-4 h-4 font-light mr-1" />
        {amount}
    </div>
)

export const EntityFieldCard: React.FC<EntityFieldCardProps> = (
    { FirstIcon, SecondIcon, firstAmount, secondAmount, name }
) => {
    return (
        <div className="w-full flex justify-between flex-row items-center">
            <Label>{name}</Label>
            <div className="flex flex-row items-center gap-1">
                <EntityCardProperty Icon={FirstIcon} amount={firstAmount} />
                <Separator className="w-4 rotate-[-75deg]" />
                <EntityCardProperty Icon={SecondIcon} amount={secondAmount} />
            </div>
        </div>
    )
};
