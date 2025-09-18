import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

export interface AdminsStatsResponse {
    total: number;
}

export const AdminsStatsDefault = {
    total: 0,
}

export async function fetchAdminsStats(): Promise<AdminsStatsResponse> {
    return await fetch(`system/stats/admins`).then((result) => {
        return result;
    });
}

export const AdminsStatsQueryFetchKey = "admins-stats";

export const useAdminsStatsQuery = () => {
    return useQuery({
        queryKey: [AdminsStatsQueryFetchKey],
        queryFn: fetchAdminsStats,
        initialData: AdminsStatsDefault
    })
}