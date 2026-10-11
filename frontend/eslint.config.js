import js from '@eslint/js';
import { defineConfig, globalIgnores } from 'eslint/config';
import prettier from 'eslint-config-prettier';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';
import tseslint from 'typescript-eslint';

// Feature-Sliced layers, lowest first: a layer may import only from the layers before it.
const LAYERS = ['shared', 'entities', 'features', 'pages', 'app'];

const layerBoundaries = LAYERS.slice(0, -1).map((layer, index) => ({
  files: [`src/${layer}/**/*.{ts,tsx}`],
  rules: {
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: LAYERS.slice(index + 1).flatMap((upper) => [`@/${upper}/**`, `**/${upper}/**`]),
            message: `"${layer}" must not import from higher layers (${LAYERS.join(' ← ')}).`,
          },
        ],
      },
    ],
  },
}));

export default defineConfig([
  globalIgnores(['dist', 'src/shared/api/generated']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.strictTypeChecked,
      tseslint.configs.stylisticTypeChecked,
      reactHooks.configs.flat['recommended-latest'],
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/restrict-template-expressions': ['error', { allowNumber: true }],
      'no-console': 'error',
    },
  },
  ...layerBoundaries,
  {
    files: ['eslint.config.js', 'postcss.config.cjs'],
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node },
  },
  prettier,
]);
