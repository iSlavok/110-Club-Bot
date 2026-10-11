import { defineConfig } from 'orval';

export default defineConfig({
  api: {
    input: { target: './openapi.json' },
    output: {
      target: './src/shared/api/generated/endpoints.ts',
      schemas: './src/shared/api/generated/model',
      mode: 'tags-split',
      client: 'react-query',
      httpClient: 'fetch',
      clean: true,
      override: {
        mutator: { path: './src/shared/api/http.ts', name: 'apiFetch' },
        fetch: { includeHttpResponseReturnType: false },
        query: { useInfinite: true, useInfiniteQueryParam: 'page' },
      },
    },
  },
});
