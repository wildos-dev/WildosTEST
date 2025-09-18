import * as React from 'react';
import { ColumnDef } from "@tanstack/react-table";
import { 
  ResponsiveEntityTable, 
  BreakpointColumnPreset 
} from '@wildosvpn/libs/responsive-table';
import { ResponsiveModal } from '@wildosvpn/libs/responsive-modal';
import { 
  ResponsiveContainer, 
  ResponsiveGrid, 
  TruncateText 
} from '@wildosvpn/libs/grid-utilities';
import { Button } from '@wildosvpn/common/components';

// Example data type
interface User {
  id: number;
  name: string;
  email: string;
  status: string;
  role: string;
  createdAt: string;
}

// Example usage of ResponsiveEntityTable
export function ResponsiveTableExample() {
  const [isModalOpen, setIsModalOpen] = React.useState(false);

  // Column definitions
  const columns: ColumnDef<User>[] = [
    {
      id: 'id',
      header: 'ID',
      accessorKey: 'id',
    },
    {
      id: 'name',
      header: 'Name',
      accessorKey: 'name',
      cell: ({ row }) => (
        <TruncateText 
          text={row.original.name} 
          maxLength={20}
          showTooltip={true}
        />
      ),
    },
    {
      id: 'email',
      header: 'Email',
      accessorKey: 'email',
      cell: ({ row }) => (
        <TruncateText 
          text={row.original.email} 
          maxLength={25}
          showTooltip={true}
        />
      ),
    },
    {
      id: 'status',
      header: 'Status',
      accessorKey: 'status',
    },
    {
      id: 'role',
      header: 'Role',
      accessorKey: 'role',
    },
    {
      id: 'createdAt',
      header: 'Created',
      accessorKey: 'createdAt',
    },
  ];

  // Breakpoint column presets
  const columnPresets: BreakpointColumnPreset<User> = {
    mobile: ['name', 'status'], // Only show essential columns on mobile
    tablet: ['name', 'email', 'status'], // Add email on tablet
    desktop: ['id', 'name', 'email', 'status', 'role', 'createdAt'], // All columns on desktop
  };

  // Sample data
  const userData: User[] = [
    {
      id: 1,
      name: 'John Doe',
      email: 'john.doe@example.com',
      status: 'active',
      role: 'admin',
      createdAt: '2024-01-15'
    },
    {
      id: 2,
      name: 'Jane Smith with a very long name that should be truncated',
      email: 'jane.smith.with.very.long.email@example.com',
      status: 'inactive',
      role: 'user',
      createdAt: '2024-01-16'
    },
  ];

  return (
    <ResponsiveContainer size="full" padding="lg">
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Responsive Components Examples</h2>
        
        {/* ResponsiveEntityTable example */}
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">ResponsiveEntityTable</h3>
          <ResponsiveEntityTable
            columns={columns}
            data={userData}
            columnPresets={columnPresets}
            enableCardView={true}
            cardViewBreakpoint="md"
            onRowClick={(user) => console.log('Row clicked:', user)}
            stickyHeader={true}
          />
        </div>

        {/* ResponsiveModal example */}
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">ResponsiveModal</h3>
          <Button onClick={() => setIsModalOpen(true)}>
            Open Responsive Modal
          </Button>
          
          <ResponsiveModal
            isOpen={isModalOpen}
            onOpenChange={setIsModalOpen}
            title="Example Modal"
            description="This modal adapts to screen size"
            size="md"
            breakpoint="md"
            footer={
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsModalOpen(false)}>
                  Save
                </Button>
              </div>
            }
          >
            <div className="space-y-4">
              <p>This is the modal content that will be displayed differently based on screen size:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>On large screens (md+): Shows as a centered dialog</li>
                <li>On small screens: Shows as a bottom drawer</li>
                <li>Content scrolls properly on both layouts</li>
                <li>Footer actions remain accessible</li>
              </ul>
            </div>
          </ResponsiveModal>
        </div>

        {/* ResponsiveGrid example */}
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">ResponsiveGrid</h3>
          <ResponsiveGrid
            cols={{ default: 1, sm: 2, md: 3, lg: 4 }}
            gap="md"
          >
            {Array.from({ length: 8 }, (_, i) => (
              <div
                key={i}
                className="bg-muted rounded-lg p-4 text-center"
              >
                <h4 className="font-medium">Card {i + 1}</h4>
                <TruncateText
                  text={`This is a longer description for card ${i + 1} that might be truncated`}
                  maxLength={30}
                  showTooltip={true}
                />
              </div>
            ))}
          </ResponsiveGrid>
        </div>
      </div>
    </ResponsiveContainer>
  );
}

// Custom card renderer example
export function CustomCardRenderer({ row, onRowClick }: any) {
  return (
    <div
      className="border rounded-lg p-4 space-y-2 cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onRowClick?.(row)}
    >
      <div className="flex justify-between items-start">
        <h3 className="font-semibold">{(row as any).name}</h3>
        <span className={`px-2 py-1 text-xs rounded ${
          (row as any).status === 'active' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {(row as any).status}
        </span>
      </div>
      <p className="text-sm text-muted-foreground">
        <TruncateText text={(row as any).email} maxLength={30} />
      </p>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Role: {(row as any).role}</span>
        <span>{(row as any).createdAt}</span>
      </div>
    </div>
  );
}