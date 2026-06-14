import js from '@eslint/js';
import globals from 'globals';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';

/**
 * Flat config (ESLint 9+/10). ESLint 10 removed the legacy `.eslintrc` format
 * entirely, so this replaces the old `.eslintrc.cjs`. It is the faithful
 * equivalent: eslint:recommended + @typescript-eslint/recommended +
 * react-hooks/recommended + the react-refresh and unused-vars tweaks.
 */
export default [
  // Match the previous `--ext ts,tsx` scope: only TypeScript sources are
  // linted. Build output, the config itself, and Node `.mjs`/`.cjs` scripts
  // (which were never linted under the old eslintrc) stay excluded.
  { ignores: ['dist', '**/*.{js,cjs,mjs}'] },
  js.configs.recommended,
  ...tsPlugin.configs['flat/recommended'],
  reactHooks.configs.flat['recommended-latest'],
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      globals: globals.browser,
      parser: tsParser,
    },
    plugins: {
      'react-refresh': reactRefresh,
    },
    rules: {
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },
];
