import { Alert, Center, Loader } from '@mantine/core';
import type { ReactNode } from 'react';

import { errorMessage } from '@/shared/lib/errors';

interface QueryStateProps<T> {
  data: T | undefined;
  error: unknown;
  isPending: boolean;
  children: (data: T) => ReactNode;
}

export function QueryState<T>({ data, error, isPending, children }: QueryStateProps<T>) {
  if (isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (error || data === undefined) {
    return (
      <Alert color="red" title="Не удалось загрузить данные">
        {errorMessage(error)}
      </Alert>
    );
  }
  return children(data);
}
