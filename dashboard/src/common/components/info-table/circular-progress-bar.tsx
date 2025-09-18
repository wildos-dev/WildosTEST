import {
    TableCell,
    TableRow,
} from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import * as React from "react";

export const CircularProgressBarRow: React.FC<{
    label: string;
    value: number;
    limit: number | undefined;
}> = ({ label, value, limit }) => {
    const { t } = useTranslation()
    return (
        <TableRow>
            <TableCell>{label}</TableCell>
            <TableCell>
                {limit ? (
                    <div className="flex items-center space-x-2">
                        <div className="relative w-8 h-8">
                            <svg className="w-8 h-8 transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                    className="text-gray-300"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                    fill="none"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                                <path
                                    className="text-blue-600"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                    strokeDasharray={`${(value / limit) * 100}, 100`}
                                    strokeLinecap="round"
                                    fill="none"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                            </svg>
                        </div>
                        <span className="text-xs">{Math.round((value / limit) * 100)}%</span>
                    </div>
                ) : t("unlimited")}
            </TableCell>
        </TableRow>
    )
};
