import * as React from "react";
export const useDialog = (open = false) => React.useState<boolean>(open);
