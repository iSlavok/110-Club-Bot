import { AppShell, Burger, Group, NavLink, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconBuildingCommunity,
  IconLayoutDashboard,
  IconShieldLock,
  IconUserCog,
  IconUsers,
  type Icon,
} from '@tabler/icons-react';
import { NavLink as RouterNavLink, Outlet } from 'react-router';

import { hasPermission, useCurrentAdmin } from '@/entities/session';
import { LogoutButton } from '@/features/auth';
import type { Permission } from '@/shared/api';
import { routes } from '@/shared/config/routes';

interface NavItem {
  to: string;
  label: string;
  icon: Icon;
  permission?: Permission;
}

export const NAV_ITEMS: NavItem[] = [
  { to: routes.dashboard, label: 'Обзор', icon: IconLayoutDashboard },
  { to: routes.clubs, label: 'Клубы', icon: IconBuildingCommunity, permission: 'clubs.view' },
  { to: routes.users, label: 'Пользователи', icon: IconUsers, permission: 'users.view' },
  { to: routes.admins, label: 'Админы', icon: IconUserCog, permission: 'admins.view' },
  { to: routes.roles, label: 'Роли', icon: IconShieldLock, permission: 'admins.view' },
];

export function AppLayout() {
  const [opened, { toggle, close }] = useDisclosure();
  const me = useCurrentAdmin().data;
  const items = NAV_ITEMS.filter((item) => !item.permission || hasPermission(me, item.permission));

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 240, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="sm">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" aria-label="Меню" />
            <Text fw={700}>Клуб 110</Text>
          </Group>
          <Group gap="xs">
            <Text size="sm" c="dimmed" visibleFrom="xs">
              {me?.name}
            </Text>
            <LogoutButton />
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs">
        {items.map((item) => (
          <NavLink
            key={item.to}
            component={RouterNavLink}
            to={item.to}
            end={item.to === routes.dashboard}
            label={item.label}
            leftSection={<item.icon size={18} />}
            onClick={close}
          />
        ))}
      </AppShell.Navbar>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
