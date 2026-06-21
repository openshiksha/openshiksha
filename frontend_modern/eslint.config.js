import js from '@eslint/js';
import globals from 'globals';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import jsxA11y from 'eslint-plugin-jsx-a11y';

/**
 * Flat config (ESLint 9+/10). ESLint 10 removed the legacy `.eslintrc` format
 * entirely, so this replaces the old `.eslintrc.cjs`. It is the faithful
 * equivalent: eslint:recommended + @typescript-eslint/recommended +
 * react-hooks/recommended + jsx-a11y/recommended + the react-refresh and
 * unused-vars tweaks.
 *
 * jsx-a11y is the static accessibility gate for the WCAG 2.1 AA initiative
 * (docs/initiatives/2026-accessibility-wcag-aa.md, A11Y-2). It complements the
 * runtime axe audit (e2e/a11y.spec.ts): the lint rules catch a11y regressions
 * at author time, on every file, before they can reach a route the axe spec
 * scans. `lint` runs at `--max-warnings 0`, so every rule that fires must be
 * fixed or carry a one-line rationale below.
 */
export default [
  // Match the previous `--ext ts,tsx` scope: only TypeScript sources are
  // linted. Build output, the config itself, and Node `.mjs`/`.cjs` scripts
  // (which were never linted under the old eslintrc) stay excluded.
  { ignores: ['dist', '**/*.{js,cjs,mjs}'] },
  js.configs.recommended,
  ...tsPlugin.configs['flat/recommended'],
  reactHooks.configs.flat['recommended-latest'],
  jsxA11y.flatConfigs.recommended,
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
      // Our nested `<label>`s wrap the control plus a styled multi-`<span>` text
      // block (e.g. a bold title over a muted hint), so the accessible text sits
      // a level deeper than the rule's default `depth: 2`. These are valid,
      // correctly-associated labels — widen the text search depth rather than
      // forcing redundant htmlFor/id pairs onto already-correct markup.
      'jsx-a11y/label-has-associated-control': ['error', { depth: 3 }],
    },
  },
];
