import { Alert, Center, Stack } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';

import { getGetMeQueryKey, useLoginWithWidget, type TelegramWidgetPayload } from '@/shared/api';
import { errorMessage } from '@/shared/lib/errors';

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramWidgetPayload) => void;
  }
}

const WIDGET_SCRIPT = 'https://telegram.org/js/telegram-widget.js?22';

interface TelegramLoginButtonProps {
  botUsername: string;
  onSuccess: () => void;
}

// The official widget renders its own iframe and reports back through a global callback.
export function TelegramLoginButton({ botUsername, onSuccess }: TelegramLoginButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const login = useLoginWithWidget({
    mutation: {
      onSuccess: (admin) => {
        queryClient.setQueryData(getGetMeQueryKey(), admin);
        onSuccess();
      },
    },
  });
  const loginRef = useRef(login.mutate);
  useEffect(() => {
    loginRef.current = login.mutate;
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    window.onTelegramAuth = (user) => {
      loginRef.current({ data: user });
    };
    const script = document.createElement('script');
    script.src = WIDGET_SCRIPT;
    script.async = true;
    script.dataset.telegramLogin = botUsername;
    script.dataset.size = 'large';
    script.dataset.onauth = 'onTelegramAuth(user)';
    container.appendChild(script);
    return () => {
      container.replaceChildren();
      delete window.onTelegramAuth;
    };
  }, [botUsername]);

  return (
    <Stack>
      <Center ref={containerRef} mih={40} />
      {login.isError && <Alert color="red">{errorMessage(login.error)}</Alert>}
    </Stack>
  );
}
