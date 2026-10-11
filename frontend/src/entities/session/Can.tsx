import type { ReactNode } from 'react';

import type { Permission } from '@/shared/api';

import { usePermission } from './model';

interface CanProps {
  permission: Permission;
  children: ReactNode;
}

export function Can({ permission, children }: CanProps) {
  return usePermission(permission) ? children : null;
}
