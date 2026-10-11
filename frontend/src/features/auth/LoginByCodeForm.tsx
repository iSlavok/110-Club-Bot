import { Alert, Anchor, Button, Group, PinInput, Stack, Text } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { getGetMeQueryKey, useLoginWithCode } from '@/shared/api';
import { errorMessage } from '@/shared/lib/errors';

const CODE_LENGTH = 6;

interface LoginByCodeFormProps {
  botUsername: string;
  onSuccess: () => void;
}

export function LoginByCodeForm({ botUsername, onSuccess }: LoginByCodeFormProps) {
  const queryClient = useQueryClient();
  const [code, setCode] = useState('');
  const login = useLoginWithCode({
    mutation: {
      onSuccess: (admin) => {
        queryClient.setQueryData(getGetMeQueryKey(), admin);
        onSuccess();
      },
      onError: () => {
        setCode('');
      },
    },
  });

  const submit = (value: string) => {
    login.mutate({ data: { code: value } });
  };

  return (
    <Stack>
      <Text size="sm">
        Отправьте боту{' '}
        <Anchor href={`https://t.me/${botUsername}`} target="_blank" rel="noreferrer">
          @{botUsername}
        </Anchor>{' '}
        команду <b>/login</b> и введите код из ответа.
      </Text>
      <Group justify="center">
        <PinInput
          length={CODE_LENGTH}
          type="number"
          oneTimeCode
          autoFocus
          aria-label="Код из бота"
          value={code}
          onChange={setCode}
          onComplete={submit}
          error={login.isError}
          disabled={login.isPending}
        />
      </Group>
      {login.isError && <Alert color="red">{errorMessage(login.error)}</Alert>}
      <Button
        onClick={() => {
          submit(code);
        }}
        loading={login.isPending}
        disabled={code.length < CODE_LENGTH}
      >
        Войти
      </Button>
    </Stack>
  );
}
