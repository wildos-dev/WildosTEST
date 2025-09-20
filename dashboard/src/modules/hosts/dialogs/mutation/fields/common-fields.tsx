// No common components needed for this file
import {
    RemarkField,
    AddressField,
    PortField,
    WeightField,
} from ".";

export const CommonFields = () => (
    <div className="space-y-4 sm:space-y-6">
        <RemarkField />
        {/* Vertical stacking on mobile, horizontal on desktop */}
        <div className="flex flex-col sm:flex-row gap-4 sm:gap-2 items-start">
            <AddressField />
            <PortField />
            <WeightField />
        </div>
    </div>
)
