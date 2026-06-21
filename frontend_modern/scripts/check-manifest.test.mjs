import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

// MSO-1: the PWA manifest is a hand-written file in `public/` (Vite serves it
// verbatim). This guards that it stays valid JSON with the keys an installable
// manifest needs, and — crucially — that every icon it references actually
// exists on disk so we never ship a manifest pointing at a 404.
const publicDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'public');
const manifestPath = path.join(publicDir, 'manifest.webmanifest');

describe('PWA web app manifest', () => {
  it('exists and is valid JSON', () => {
    expect(existsSync(manifestPath)).toBe(true);
    expect(() => JSON.parse(readFileSync(manifestPath, 'utf-8'))).not.toThrow();
  });

  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));

  it('declares the required installability fields', () => {
    expect(manifest.name).toBeTruthy();
    expect(manifest.short_name).toBeTruthy();
    expect(manifest.start_url).toBe('/');
    expect(manifest.scope).toBe('/');
    expect(manifest.display).toBe('standalone');
    expect(manifest.theme_color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    expect(manifest.background_color).toMatch(/^#[0-9A-Fa-f]{6}$/);
  });

  it('ships 192 and 512 icons in both "any" and "maskable" purposes', () => {
    const byPurpose = (p) => manifest.icons.filter((i) => i.purpose === p).map((i) => i.sizes);
    expect(byPurpose('any')).toEqual(expect.arrayContaining(['192x192', '512x512']));
    expect(byPurpose('maskable')).toEqual(expect.arrayContaining(['192x192', '512x512']));
  });

  it('references only icon files that exist on disk', () => {
    for (const icon of manifest.icons) {
      const iconPath = path.join(publicDir, icon.src.replace(/^\//, ''));
      expect(existsSync(iconPath), `${icon.src} should exist`).toBe(true);
      expect(icon.type).toBe('image/png');
    }
  });
});
