import * as React from "react";
import { fetchAdmins, AdminType, AdminsQueryFetchKey } from "@wildosvpn/modules/admins";
import { columns as columnsFn } from "./columns";
import { EntityTable } from "@wildosvpn/libs/entity-table";
import { useNavigate } from "@tanstack/react-router";
import { AdminCard } from "./admin-card";
import {
    Input,
    Button,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@wildosvpn/common/components';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';

export const AdminsTable: React.FC = () => {
    const navigate = useNavigate({ from: "/admins" });
    const { t } = useTranslation();
    const [searchQuery, setSearchQuery] = React.useState('');
    const [statusFilter, setStatusFilter] = React.useState('all');
    
    const onOpen = (entity: AdminType) => {
        navigate({
            to: "/admins/$adminId",
            params: { adminId: entity.username },
        })
    }

    const onEdit = (entity: AdminType) => {
        navigate({
            to: "/admins/$adminId/edit",
            params: { adminId: entity.username },
        })
    }

    const onDelete = (entity: AdminType) => {
        navigate({
            to: "/admins/$adminId/delete",
            params: { adminId: entity.username },
        })
    }

    const handleCreateClick = () => {
        navigate({ to: "/admins/create" });
    };

    const columns = columnsFn({ onEdit, onDelete, onOpen });
    const cardActions = { onEdit, onDelete, onOpen };

    return (
        <div className="space-y-6">
            {/* Filters and Create Button */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <div className="flex flex-col sm:flex-row gap-4 flex-1">
                    {/* Search Input */}
                    <div className="relative flex-1 max-w-md">
                        <Icon name="Search" className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder={t("placeholders.search-filter")}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                            data-testid="input-search-admins"
                        />
                    </div>

                    {/* Status Filter */}
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                        <SelectTrigger className="w-48" data-testid="select-status-filter">
                            <SelectValue placeholder={t('status')} />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all" data-testid="select-option-all">All</SelectItem>
                            <SelectItem value="enabled" data-testid="select-option-enabled">Enabled</SelectItem>
                            <SelectItem value="disabled" data-testid="select-option-disabled">Disabled</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Create Button */}
                <Button onClick={handleCreateClick} className="shrink-0" data-testid="button-create-admin">
                    <Icon name="Plus" className="h-4 w-4 mr-2" />
                    {t('create')}
                </Button>
            </div>

            <EntityTable
                fetchEntity={fetchAdmins}
                columns={columns}
                primaryFilter="username"
                entityKey={AdminsQueryFetchKey}
                onCreate={handleCreateClick}
                onOpen={onOpen}
                CardComponent={AdminCard}
                cardActions={cardActions}
            />
        </div>
    );
};
