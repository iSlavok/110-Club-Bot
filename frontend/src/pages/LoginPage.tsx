import { Center, Divider, Paper, Stack, Text, Title } from '@mantine/core';
import { Navigate, useLocation, useNavigate } from 'react-router';

import { useCurrentAdmin } from '@/entities/session';
import { LoginByCodeForm, TelegramLoginButton } from '@/features/auth';
import { useGetAuthConfig } from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { QueryState } from '@/shared/ui/QueryState';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const me = useCurrentAdmin();
  const config = useGetAuthConfig();
  const from = (location.state as { from?: string } | null)?.from ?? routes.home;

  if (me.data) {
    return <Navigate to={from} replace />;
  }

  const enter = () => {
    void navigate(from, { replace: true });
  };

  return (
    <Center mih="100vh" p="md">
      <Paper withBorder shadow="sm" radius="lg" p="xl" w="100%" maw={420}>
        <Stack>
          <div>
            <Title order={2}>Клуб 110</Title>
            <Text c="dimmed" size="sm">
              Вход в админку
            </Text>
          </div>
          <QueryState data={config.data} error={config.error} isPending={config.isPending}>
            {(authConfig) => (
              <Stack>
                <LoginByCodeForm botUsername={authConfig.bot_username} onSuccess={enter} />
                {authConfig.widget_enabled && (
                  <>
                    <Divider label="или" />
                    <TelegramLoginButton botUsername={authConfig.bot_username} onSuccess={enter} />
                  </>
                )}
              </Stack>
            )}
          </QueryState>
        </Stack>
      </Paper>
    </Center>
  );
}
