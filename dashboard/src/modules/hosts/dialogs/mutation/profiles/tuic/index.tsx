import {
    CommonFields,
} from "../../fields";
import {
    TlsFields
} from "../../sections";
import {
    Accordion,
} from "@wildosvpn/common/components";

export const TuicProfileFields = () => {
    return (
        <div className="space-y-4 sm:space-y-6">
            <CommonFields />
            <Accordion className="space-y-4 sm:space-y-2" type="single" collapsible>
                <TlsFields />
            </Accordion>
        </div>
    )
}

export * from "./schema";
export * from "./default";
