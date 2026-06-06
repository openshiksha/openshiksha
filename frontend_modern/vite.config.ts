import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test-setup.ts'],
    // Vitest runs unit tests only — Playwright owns e2e/ (see playwright.config.ts).
    // `scripts/` holds dev-tooling Node scripts (e.g. the IW-8 widget
    // scaffolder); their tests live next to the script so coverage stays
    // local and discoverable.
    include: ['src/**/*.{test,spec}.{ts,tsx}', 'scripts/**/*.{test,spec}.mjs'],
    exclude: ['node_modules/**', 'dist/**', 'e2e/**'],
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary', 'html', 'lcov', 'json-summary'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.d.ts',
        'src/**/*.test.{ts,tsx}',
        'src/**/__tests__/**',
        'src/test-setup.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      // Thresholds match the current measured floor. Ratchet these up as new
      // tests land — never lower without a recorded reason.
      //
      // 2026-06-01: re-baselined funcs 18→6 and branches 40→8 after upgrading
      // Vitest 1→4 (security audit fix). Vitest 4's v8 provider uses AST-aware
      // remapping, which counts branches/functions more accurately than v1 did;
      // the same 38 tests now measure 6.98% funcs / 8.52% branches (was 18.64% /
      // 45.77%). No tests were lost — only the measurement changed. Lines and
      // statements are unaffected (10.43%).
      // (2026-05-30 baseline under Vitest 1: 10.24% lines, 18.64% funcs, 45.77% branches.)
      thresholds: {
        lines: 10,
        statements: 10,
        functions: 6,
        branches: 8,
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/features': path.resolve(__dirname, './src/features'),
      '@/shared': path.resolve(__dirname, './src/shared'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/api': path.resolve(__dirname, './src/api'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
