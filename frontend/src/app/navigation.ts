import {
  IconAdjustments,
  IconBuildingCommunity,
  IconCalendarEvent,
  IconLayoutDashboard,
  IconRefresh,
  IconSettings,
  IconShieldLock,
  IconUserCog,
  IconUsers,
  type Icon,
} from '@tabler/icons-react';

import type { Permission } from '@/shared/api';
import { routes } from '@/shared/config/routes';

export interface NavItem {
  to: string;
  label: string;
  icon: Icon;
  permission?: Permission;
  /** Active only on this exact path, not on the paths below it. */
  end?: boolean;
}

export const GLOBAL_NAV: NavItem[] = [
  { to: routes.clubs, label: 'Клубы', icon: IconBuildingCommunity, permission: 'clubs.view' },
  { to: routes.users, label: 'Пользователи', icon: IconUsers, permission: 'users.view' },
  { to: routes.admins, label: 'Админы', icon: IconUserCog, permission: 'admins.view' },
  { to: routes.roles, label: 'Роли', icon: IconShieldLock, permission: 'admins.view' },
  { to: routes.settings, label: 'Настройки бота', icon: IconAdjustments },
];

/** Sections inside a club; the whole club area needs `clubs.view`. */
export function clubNav(clubId: number): NavItem[] {
  return [
    { to: routes.club(clubId), label: 'Обзор', icon: IconLayoutDashboard, end: true },
    { to: routes.clubBlocks(clubId), label: 'Блоки', icon: IconCalendarEvent },
    { to: routes.clubSync(clubId), label: 'Синк таблицы', icon: IconRefresh },
    { to: routes.clubSettings(clubId), label: 'Настройки клуба', icon: IconSettings },
  ];
}
