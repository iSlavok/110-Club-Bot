import { ActionIcon, Tooltip } from '@mantine/core';
import { IconLogout } from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';

import { useLogout } from '@/shared/api';
import { routes } from '@/shared/config/routes';

export function LogoutButton() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const logout = useLogout({
    mutation: {
      onSettled: () => {
        queryClient.clear();
        void navigate(routes.login, { replace: true });
      },
    },
  });

  return (
    <Tooltip label="Выйти">
      <ActionIcon
        variant="subtle"
        color="gray"
        size="lg"
        aria-label="Выйти"
        loading={logout.isPending}
        onClick={() => {
          logout.mutate();
        }}
      >
        <IconLogout size={20} />
      </ActionIcon>
    </Tooltip>
  );
}
