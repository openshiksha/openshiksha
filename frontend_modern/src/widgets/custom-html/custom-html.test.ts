/**
 * Tests for the `custom-html` escape-hatch widget (IW-7).
 *
 * Coverage focuses on the *module surface* (what the host bakes into
 * the srcdoc): kind identity, registry round-trip, render-source
 * contents (admin-only labelling, inline-script re-execution, empty
 * config fallback). The in-sandbox render runs inside the iframe and
 * is exercised end-to-end by the host srcdoc tests + the /design page.
 */

import { describe, expect, it } from 'vitest';
import customHtml from './index';
import { getWidgetModule } from '../registry';

describe('custom-html widget module', () => {
  it('declares the expected identity + version', () => {
    expect(customHtml.kind).toBe('custom-html');
    expect(customHtml.version).toBe(1);
  });

  it('is explanatory (not answer-producing)', () => {
    expect(customHtml.meta.answerProducing).toBe(false);
  });

  it('is admin-only — title carries the gating affordance', () => {
    // Until IW-5's gallery enforces the restriction programmatically,
    // the title is what stops a teacher picking this kind by mistake.
    expect(customHtml.meta.title).toMatch(/admin/i);
  });

  it('is registered in the SDK registry under its kind key', () => {
    expect(getWidgetModule('custom-html')).toBe(customHtml);
  });

  it('renderSource gracefully handles a missing `html` field', () => {
    expect(customHtml.renderSource).toContain('no `html` field');
  });

  it('renderSource re-executes inline scripts after innerHTML insertion', () => {
    // The script re-execution pattern is the load-bearing trick of the
    // widget (innerHTML alone leaves <script> tags inert). Pin the
    // distinguishing markers so a refactor cannot silently drop the
    // re-execution loop.
    expect(customHtml.renderSource).toContain('querySelectorAll');
    expect(customHtml.renderSource).toContain('replaceChild');
    expect(customHtml.renderSource).toContain('innerHTML');
  });

  it('renderSource preserves script attributes (src, type, …) so vendor URLs still load', () => {
    expect(customHtml.renderSource).toMatch(/attributes/);
    // async = false keeps src-style scripts loading in document order.
    expect(customHtml.renderSource).toMatch(/async\s*=\s*false/);
  });
});
