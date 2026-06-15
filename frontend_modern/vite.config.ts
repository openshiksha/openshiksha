import { defineConfig, type PluginOption } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'path';

// `rollup-plugin-visualizer` is only used in `--mode analyze`. We dynamic-
// import it inside the factory so missing it never breaks a normal `dev` /
// `build` — Docker images that omit dev deps, fresh clones before
// `npm install`, etc. still boot cleanly.
async function loadVisualizer(): Promise<PluginOption | null> {
  try {
    const mod = await import('rollup-plugin-visualizer');
    return mod.visualizer({
      filename: 'dist/stats.html',
      template: 'treemap',
      gzipSize: true,
      brotliSize: true,
    });
  } catch {
    console.warn(
      '[vite.config] --mode analyze requested but rollup-plugin-visualizer is not installed; skipping.',
    );
    return null;
  }
}

// https://vitejs.dev/config/
export default defineConfig(async ({ mode }) => ({
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
      // The PWA service-worker hook is a build-time virtual module; stub it so
      // importing PwaUpdater/App under Vitest resolves cleanly (MSO-3).
      'virtual:pwa-register/react': path.resolve(__dirname, './src/test-stubs/pwa-register-react.ts'),
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
  plugins: [
    react(),
    // MSO-3: service worker for offline app-shell tolerance. We ship a
    // hand-written manifest.webmanifest (MSO-1), so `manifest: false` — never
    // let the plugin emit a second one. Registration is manual + prod-only in
    // main.tsx (`injectRegister: null`) so dev/tests never register a SW.
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: null,
      manifest: false,
      // Dev: keep the SW disabled so HMR/caching stays predictable.
      devOptions: { enabled: false },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff,woff2}'],
        // Deep links boot offline from the precached shell. /api must never be
        // served the shell (principle 2) — the persisted React Query cache
        // (MSO-4), not Workbox, owns API read-tolerance.
        navigateFallback: 'index.html',
        navigateFallbackDenylist: [/^\/api/],
        runtimeCaching: [
          {
            // Google Fonts binaries (Inter / Fraunces / Noto Devanagari) so
            // text + Devanagari render offline.
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-webfonts',
              expiration: { maxEntries: 30, maxAgeSeconds: 60 * 60 * 24 * 365 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // KaTeX CDN (CSS + fonts) so math renders offline.
            urlPattern: /^https:\/\/cdn\.jsdelivr\.net\/npm\/katex.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'katex-cdn',
              expiration: { maxEntries: 40, maxAgeSeconds: 60 * 60 * 24 * 365 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Explicit: never cache API responses in the service worker.
            urlPattern: ({ url }) => url.pathname.startsWith('/api'),
            handler: 'NetworkOnly',
          },
        ],
      },
    }),
    ...(mode === 'analyze' ? [await loadVisualizer()].filter(Boolean) : []),
  ],
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
    // Honest current ceiling — entry chunk pre-PERF-03 sits around 850 kB.
    // PERF-03 (route-level lazy) will drop this; PERF-06 enforces a CI budget.
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        // Rolldown requires a function form. Group framework-level deps into
        // long-cacheable vendor chunks so feature code can change without
        // re-downloading the framework.
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return undefined;
          if (/[\\/]node_modules[\\/](react|react-dom|react-router|react-router-dom|scheduler)[\\/]/.test(id)) {
            return 'vendor-react';
          }
          if (/[\\/]node_modules[\\/]@tanstack[\\/]react-query-devtools[\\/]/.test(id)) {
            // Dev-only. main.tsx guards the import with `import.meta.env.DEV`
            // so production builds tree-shake it out entirely; keeping a
            // dedicated chunk name here means a dev build also doesn't
            // pollute the long-cacheable vendor-query chunk.
            return 'devtools-react-query';
          }
          if (/[\\/]node_modules[\\/]@tanstack[\\/]/.test(id)) {
            return 'vendor-query';
          }
          if (/[\\/]node_modules[\\/](katex|react-katex)[\\/]/.test(id)) {
            return 'vendor-katex';
          }
          if (/[\\/]node_modules[\\/]dompurify[\\/]/.test(id)) {
            return 'vendor-dompurify';
          }
          return undefined;
        },
      },
    },
  },
}));
