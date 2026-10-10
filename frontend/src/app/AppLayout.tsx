import { AppShell, Burger, Divider, Group, NavLink, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { NavLink as RouterNavLink, Outlet } from 'react-router';

import { useClubChoice } from '@/entities/club';
import { hasPermission, useCurrentAdmin } from '@/entities/session';
import { LogoutButton } from '@/features/auth';
import { ClubSwitcher } from '@/features/club';
import { useGetClub } from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { useRouteClubId } from '@/shared/lib/club-id';

import { clubNav, GLOBAL_NAV, type NavItem } from './navigation';

function NavItems({ items, onNavigate }: { items: NavItem[]; onNavigate: () => void }) {
  return items.map((item) => (
    <NavLink
      key={item.to}
      component={RouterNavLink}
      to={item.to}
      end={item.end}
      label={item.label}
      leftSection={<item.icon size={18} />}
      onClick={onNavigate}
    />
  ));
}

export function AppLayout() {
  const [opened, { toggle, close }] = useDisclosure();
  const me = useCurrentAdmin().data;
  const canViewClubs = hasPermission(me, 'clubs.view');
  const choice = useClubChoice(canViewClubs);
  // With a single club the whole panel lives inside it, wherever the URL points.
  const routeClubId = useRouteClubId();
  const clubId = canViewClubs ? (routeClubId ?? choice.onlyClub?.id ?? null) : null;
  const club = useGetClub(clubId ?? 0, { query: { enabled: clubId !== null } }).data;

  const allowed = (item: NavItem) => !item.permission || hasPermission(me, item.permission);
  const globalItems = GLOBAL_NAV.filter(
    (item) => allowed(item) && !(item.to === routes.clubs && choice.onlyClub),
  );
  const canSwitch = choice.clubs.length > 1 || hasPermission(me, 'clubs.edit');

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 240, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" aria-label="Меню" />
            {club && canSwitch ? (
              <ClubSwitcher title={club.title} currentId={club.id} clubs={choice.clubs} />
            ) : (
              <Text fw={700} truncate>
                {club?.title ?? 'Клуб 110'}
              </Text>
            )}
          </Group>
          <Group gap="xs" wrap="nowrap">
            <Text size="sm" c="dimmed" visibleFrom="xs">
              {me?.name}
            </Text>
            <LogoutButton />
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs">
        {clubId !== null && (
          <>
            <NavItems items={clubNav(clubId).filter(allowed)} onNavigate={close} />
            {globalItems.length > 0 && <Divider my="xs" label="Общее" labelPosition="left" />}
          </>
        )}
        <NavItems items={globalItems} onNavigate={close} />
      </AppShell.Navbar>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
