#!/usr/bin/env node
/**
 * Single-shot performance measurement against the local preview build under
 * "budget Android on Indian 3G" emulation. Uses Playwright + CDP to set:
 *   - Network: Slow 4G (400 ms RTT, 400 kbps down, 400 kbps up) — closer to
 *     real Indian mobile than Chrome's "Slow 3G" which under-states download.
 *   - CPU: 4x slowdown — proxies a low-end Snapdragon.
 *
 * Reports FCP, LCP, total page weight, and a per-resource breakdown so we can
 * see whether fonts, JS, or CSS dominates the critical path. This informs
 * whether PERF-05 (font self-hosting) is worth the operational cost.
 *
 * Run: `node scripts/measure-perf.mjs http://localhost:4173/login`
 */
import { chromium } from 'playwright';

const URL = process.argv[2] ?? 'http://localhost:4173/login';

const fmt = (n) => (n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} kB`);
const ms = (n) => `${Math.round(n)} ms`;

async function main() {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 360, height: 740 },
    userAgent:
      'Mozilla/5.0 (Linux; Android 10; SM-A105F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36',
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
  });
  const page = await ctx.newPage();
  const client = await ctx.newCDPSession(page);

  // Slow 4G profile — Chrome DevTools defaults.
  await client.send('Network.enable');
  await client.send('Network.emulateNetworkConditions', {
    offline: false,
    latency: 400,
    downloadThroughput: (400 * 1024) / 8,
    uploadThroughput: (400 * 1024) / 8,
  });
  await client.send('Emulation.setCPUThrottlingRate', { rate: 4 });

  // Collect resource sizes by URL.
  const resources = new Map();
  page.on('response', async (resp) => {
    try {
      const url = resp.url();
      const hdrs = resp.headers();
      const lenHeader = Number(hdrs['content-length'] ?? 0);
      // Fall back to body length for chunk-encoded responses.
      let size = lenHeader;
      if (!size) {
        try {
          const body = await resp.body();
          size = body.length;
        } catch {
          size = 0;
        }
      }
      resources.set(url, {
        size,
        type: hdrs['content-type']?.split(';')[0] ?? '',
        status: resp.status(),
      });
    } catch {
      /* ignore */
    }
  });

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'load', timeout: 60_000 });
  const loadMs = Date.now() - t0;

  // Wait a beat for the LCP entry to settle (longest contentful paint is
  // emitted after layout).
  await page.waitForTimeout(1500);

  const paint = await page.evaluate(() => {
    const entries = performance.getEntriesByType('paint');
    const fcp = entries.find((e) => e.name === 'first-contentful-paint')?.startTime ?? null;
    const navi = performance.getEntriesByType('navigation')[0];
    const lcp = new Promise((resolve) => {
      let last = null;
      try {
        const po = new PerformanceObserver((list) => {
          const e = list.getEntries();
          last = e[e.length - 1]?.startTime ?? last;
        });
        po.observe({ type: 'largest-contentful-paint', buffered: true });
      } catch {
        /* ignore */
      }
      // Resolve synchronously from `buffered: true` if anything is there.
      setTimeout(() => {
        const all = performance.getEntriesByType('largest-contentful-paint');
        resolve(all[all.length - 1]?.startTime ?? last);
      }, 0);
    });
    return {
      fcp,
      lcp: lcp,
      domContentLoaded: navi?.domContentLoadedEventEnd ?? null,
      loadEvent: navi?.loadEventEnd ?? null,
      navigationStart: navi?.startTime ?? 0,
    };
  });
  const lcp = await paint.lcp;

  // Bucket resources.
  const buckets = { js: [], css: [], font: [], image: [], html: [], other: [] };
  let total = 0;
  for (const [url, info] of resources) {
    total += info.size;
    const t = info.type;
    if (t.includes('javascript') || url.endsWith('.js')) buckets.js.push({ url, size: info.size });
    else if (t.includes('css') || url.endsWith('.css')) buckets.css.push({ url, size: info.size });
    else if (t.includes('font') || /\.(woff2?|ttf|otf)(\?|$)/.test(url)) buckets.font.push({ url, size: info.size });
    else if (t.startsWith('image/') || /\.(png|jpg|jpeg|svg|gif|webp)(\?|$)/.test(url)) buckets.image.push({ url, size: info.size });
    else if (t.includes('html')) buckets.html.push({ url, size: info.size });
    else buckets.other.push({ url, size: info.size });
  }
  const bucketTotal = (b) => b.reduce((s, r) => s + r.size, 0);

  console.log(`\n=== ${URL} (Slow 4G + 4x CPU, mobile UA) ===`);
  console.log(`FCP:                ${ms(paint.fcp ?? NaN)}`);
  console.log(`LCP:                ${ms(lcp ?? NaN)}`);
  console.log(`DOMContentLoaded:   ${ms(paint.domContentLoaded ?? NaN)}`);
  console.log(`load event:         ${ms(paint.loadEvent ?? NaN)}`);
  console.log(`page.goto wall:     ${ms(loadMs)}`);
  console.log(`\n--- transferred bytes by type ---`);
  for (const [k, b] of Object.entries(buckets)) {
    if (!b.length) continue;
    console.log(`${k.padEnd(8)} ${b.length.toString().padStart(3)} req   ${fmt(bucketTotal(b)).padStart(10)}`);
  }
  console.log(`${'total'.padEnd(8)} ${resources.size.toString().padStart(3)} req   ${fmt(total).padStart(10)}`);

  console.log(`\n--- per-resource (>= 5 kB) ---`);
  const all = [...resources.entries()]
    .map(([url, info]) => ({ url, ...info }))
    .filter((r) => r.size >= 5 * 1024)
    .sort((a, b) => b.size - a.size);
  for (const r of all) {
    const short = r.url.replace(/^https?:\/\/[^/]+/, '').slice(0, 90);
    console.log(`${fmt(r.size).padStart(10)}  ${short}`);
  }

  console.log(`\n--- font requests (any size) ---`);
  for (const r of buckets.font.sort((a, b) => b.size - a.size)) {
    const short = r.url.replace(/^https?:\/\/[^/]+/, '').slice(0, 90);
    console.log(`${fmt(r.size).padStart(10)}  ${short}`);
  }

  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
