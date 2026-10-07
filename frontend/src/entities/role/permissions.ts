import type { PermissionGroup, PermissionResponse } from '@/shared/api';

export const PERMISSION_GROUP_TITLES: Record<PermissionGroup, string> = {
  clubs: 'Клубы',
  users: 'Пользователи',
  admins: 'Админы и роли',
};

export function groupPermissions(
  catalog: PermissionResponse[],
): [PermissionGroup, PermissionResponse[]][] {
  const groups = new Map<PermissionGroup, PermissionResponse[]>();
  for (const permission of catalog) {
    groups.set(permission.group, [...(groups.get(permission.group) ?? []), permission]);
  }
  return [...groups.entries()];
}
