import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';

interface SystemStatus {
  version: string;
  database_connected: boolean;
  redis_connected: boolean;
  grobid_connected: boolean;
  worker_running: boolean;
}

interface UserStats {
  total_users: number;
  active_users: number;
  blocked_users: number;
}

interface StorageStats {
  total_bytes: number;
  used_bytes: number;
  file_count: number;
}

interface UserInfo {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  is_blocked: boolean;
  storage_quota_bytes: number;
  created_at: string;
}

interface Settings {
  maintenance_mode: boolean;
  registration_enabled: boolean;
  max_upload_size_mb: number;
  default_quota_gb: number;
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-3 h-3 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-sm">{label}: {ok ? 'OK' : 'Failed'}</span>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function AdminPage() {
  const queryClient = useQueryClient();

  // Fetch system status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['admin', 'status'],
    queryFn: async () => {
      const response = await apiClient.get<SystemStatus>('/admin/status');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch user stats
  const { data: userStats } = useQuery({
    queryKey: ['admin', 'stats', 'users'],
    queryFn: async () => {
      const response = await apiClient.get<UserStats>('/admin/stats/users');
      return response.data;
    },
  });

  // Fetch storage stats
  const { data: storageStats } = useQuery({
    queryKey: ['admin', 'stats', 'storage'],
    queryFn: async () => {
      const response = await apiClient.get<StorageStats>('/admin/stats/storage');
      return response.data;
    },
  });

  // Fetch users list
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: async () => {
      const response = await apiClient.get<UserInfo[]>('/admin/users');
      return response.data;
    },
  });

  // Fetch settings
  const { data: settings } = useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: async () => {
      const response = await apiClient.get<Settings>('/admin/settings');
      return response.data;
    },
  });

  // Block user mutation
  const blockUserMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: string; reason: string }) => {
      const response = await apiClient.post(`/admin/users/${userId}/block?reason=${encodeURIComponent(reason)}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast.success('User blocked successfully');
    },
    onError: () => {
      toast.error('Failed to block user');
    },
  });

  // Unblock user mutation
  const unblockUserMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await apiClient.post(`/admin/users/${userId}/unblock`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast.success('User unblocked successfully');
    },
    onError: () => {
      toast.error('Failed to unblock user');
    },
  });

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: async (newSettings: Settings) => {
      const response = await apiClient.put('/admin/settings', newSettings);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'settings'] });
      toast.success('Settings updated successfully');
    },
    onError: () => {
      toast.error('Failed to update settings');
    },
  });

  const handleBlockUser = (userId: string) => {
    const reason = prompt('Enter reason for blocking:');
    if (reason) {
      blockUserMutation.mutate({ userId, reason });
    }
  };

  const handleUnblockUser = (userId: string) => {
    if (confirm('Are you sure you want to unblock this user?')) {
      unblockUserMutation.mutate(userId);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold mb-6">Admin Panel</h1>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          {statusLoading ? (
            <Skeleton className="h-20 w-full" />
          ) : status ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusBadge ok={status.database_connected} label="Database" />
              <StatusBadge ok={status.redis_connected} label="Redis" />
              <StatusBadge ok={status.grobid_connected} label="GROBID" />
              <StatusBadge ok={status.worker_running} label="Worker" />
              <div className="text-sm text-muted-foreground col-span-full mt-2">
                Version: {status.version}
              </div>
            </div>
          ) : (
            <p className="text-red-500">Failed to load system status</p>
          )}
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats?.total_users ?? '-'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats?.active_users ?? '-'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Blocked Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats?.blocked_users ?? '-'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {storageStats ? formatBytes(storageStats.used_bytes) : '-'}
            </div>
            <div className="text-xs text-muted-foreground">
              {storageStats?.file_count ?? 0} files
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Settings */}
      {settings && (
        <Card>
          <CardHeader>
            <CardTitle>System Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Maintenance Mode</label>
              <input
                type="checkbox"
                checked={settings.maintenance_mode}
                onChange={(e) =>
                  updateSettingsMutation.mutate({
                    ...settings,
                    maintenance_mode: e.target.checked,
                  })
                }
                className="h-4 w-4"
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Registration Enabled</label>
              <input
                type="checkbox"
                checked={settings.registration_enabled}
                onChange={(e) =>
                  updateSettingsMutation.mutate({
                    ...settings,
                    registration_enabled: e.target.checked,
                  })
                }
                className="h-4 w-4"
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Max Upload Size (MB)</label>
              <Input
                type="number"
                value={settings.max_upload_size_mb}
                onChange={(e) =>
                  updateSettingsMutation.mutate({
                    ...settings,
                    max_upload_size_mb: parseInt(e.target.value),
                  })
                }
                className="w-32"
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Default Quota (GB)</label>
              <Input
                type="number"
                value={settings.default_quota_gb}
                onChange={(e) =>
                  updateSettingsMutation.mutate({
                    ...settings,
                    default_quota_gb: parseInt(e.target.value),
                  })
                }
                className="w-32"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          {usersLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Display Name</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Quota</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users?.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.display_name || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.is_blocked ? (
                        <Badge variant="destructive">Blocked</Badge>
                      ) : (
                        <Badge variant="outline">Active</Badge>
                      )}
                    </TableCell>
                    <TableCell>{formatBytes(user.storage_quota_bytes)}</TableCell>
                    <TableCell>
                      {new Date(user.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {user.is_blocked ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUnblockUser(user.id)}
                        >
                          Unblock
                        </Button>
                      ) : (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleBlockUser(user.id)}
                        >
                          Block
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {users?.length === 0 && (
            <p className="text-center text-muted-foreground py-8">No users found</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
