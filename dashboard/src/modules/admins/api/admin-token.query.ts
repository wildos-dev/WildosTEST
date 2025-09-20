import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

export async function fetchAdminToken(): Promise<{ token: string }> {
    return fetch('/admins/current/token');
}

export const AdminTokenQueryFetchKey = "admin-token";

export const useAdminTokenQuery = () => {
    return useQuery({
        queryKey: [AdminTokenQueryFetchKey],
        queryFn: fetchAdminToken,
        initialData: { token: '' }
    })
}