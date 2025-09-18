
import { DateField } from "@wildosvpn/common/components";
import * as React from "react";

export const ActivationDeadlineField: React.FC = () => {
    return <DateField name="activation_deadline" label="page.users.activation_deadline" />;
};
