import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

// MPN-3: the Web Push handler is a hand-written file in `public/` that the
// service worker pulls in via `workbox.importScripts`. This guards that the
// file exists, registers the two listeners push actually needs, and that
// vite.config.ts still imports it — so we never ship a SW that silently drops
// notifications.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const handlerPath = path.join(root, 'public', 'push-handler.js');
const viteConfigPath = path.join(root, 'vite.config.ts');

describe('Web Push service-worker handler', () => {
  it('push-handler.js exists in public/', () => {
    expect(existsSync(handlerPath)).toBe(true);
  });

  const handler = existsSync(handlerPath) ? readFileSync(handlerPath, 'utf-8') : '';

  it('registers push and notificationclick listeners', () => {
    expect(handler).toMatch(/addEventListener\(['"]push['"]/);
    expect(handler).toMatch(/addEventListener\(['"]notificationclick['"]/);
  });

  it('shows a notification and deep-links on click', () => {
    expect(handler).toContain('showNotification');
    expect(handler).toMatch(/clients\.(openWindow|matchAll)/);
  });

  it('is imported by the service worker via workbox.importScripts', () => {
    const cfg = readFileSync(viteConfigPath, 'utf-8');
    expect(cfg).toMatch(/importScripts:\s*\[[^\]]*['"]push-handler\.js['"]/);
  });
});
