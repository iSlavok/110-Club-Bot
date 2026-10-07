import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import '@mantine/notifications/styles.css';

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router';

import { Providers } from '@/app/Providers';
import { createQueryClient } from '@/app/query-client';
import { appRoutes } from '@/app/router';

const root = document.getElementById('root');
if (!root) {
  throw new Error('Root element #root is missing in index.html');
}

createRoot(root).render(
  <StrictMode>
    <Providers queryClient={createQueryClient()}>
      <RouterProvider router={createBrowserRouter(appRoutes)} />
    </Providers>
  </StrictMode>,
);
