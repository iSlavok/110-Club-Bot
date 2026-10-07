import { fileURLToPath } from 'node:url';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  // Internal admin panel: one cached bundle, mostly Mantine; splitting it would not speed anything up.
  build: { chunkSizeWarningLimit: 1024 },
  server: {
    port: 5173,
    // Same origin as in production (nginx in the web image proxies /api), so the session cookie works without CORS.
    proxy: { '/api': 'http://localhost:8000' },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    restoreMocks: true,
  },
});
