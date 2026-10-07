import { useGetMe, type CurrentAdminResponse, type Permission } from '@/shared/api';

export function useCurrentAdmin() {
  return useGetMe({ query: { retry: false, staleTime: 5 * 60_000 } });
}

export function hasPermission(
  admin: CurrentAdminResponse | undefined,
  permission: Permission,
): boolean {
  return admin?.permissions.includes(permission) ?? false;
}

export function usePermission(permission: Permission): boolean {
  return hasPermission(useCurrentAdmin().data, permission);
}

/** Roles and permissions an admin may hand out: never more than they have themselves. */
export function canGrant(
  admin: CurrentAdminResponse | undefined,
  permissions: readonly Permission[],
): boolean {
  return permissions.every((permission) => hasPermission(admin, permission));
}
