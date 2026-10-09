import { Button, Menu } from '@mantine/core';
import { IconCheck, IconChevronDown, IconList } from '@tabler/icons-react';
import { Link } from 'react-router';

import type { ClubResponse } from '@/shared/api';
import { routes } from '@/shared/config/routes';

interface ClubSwitcherProps {
  title: string;
  currentId: number;
  clubs: ClubResponse[];
}

export function ClubSwitcher({ title, currentId, clubs }: ClubSwitcherProps) {
  return (
    <Menu position="bottom-start" shadow="md" width={260}>
      <Menu.Target>
        <Button
          variant="subtle"
          color="gray"
          rightSection={<IconChevronDown size={16} />}
          aria-label="Сменить клуб"
          px="xs"
          fw={700}
          fz="md"
        >
          {title}
        </Button>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>Клубы</Menu.Label>
        {clubs.map((club) => (
          <Menu.Item
            key={club.id}
            component={Link}
            to={routes.club(club.id)}
            rightSection={club.id === currentId ? <IconCheck size={14} /> : null}
            c={club.is_active ? undefined : 'dimmed'}
          >
            {club.title}
          </Menu.Item>
        ))}
        <Menu.Divider />
        <Menu.Item component={Link} to={routes.clubs} leftSection={<IconList size={14} />}>
          Все клубы
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
}
