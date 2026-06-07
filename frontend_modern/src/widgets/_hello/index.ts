/**
 * `_hello` — the IW-1 end-to-end proof widget.
 *
 * This is the simplest possible widget: it renders `Widget runtime alive ·
 * kind = _hello` (echoing the kind it was booted with) and nothing else. Its
 * job is to prove that the SDK → host → sandbox → runtime → render loop
 * works, so every future widget can build on a known-good foundation.
 *
 * The leading underscore signals "framework-internal / reference" — it is
 * not surfaced in the teacher gallery (IW-5 will filter `kind.startsWith('_')`
 * out). The Studio's scene-runner (`studio-scene`, IW-9) is the *user-visible*
 * pure-data widget; `_hello` is just for testing the contract.
 *
 * Render uses **vanilla DOM**, not React, because IW-1c's runtime does not
 * bootstrap React inside the sandbox — IW-2 lands React-in-sandbox alongside
 * the `thermo-piston` widget. Vanilla DOM is enough to prove the loop.
 */

import { defineWidget } from '../_sdk/defineWidget';

export default defineWidget({
  kind: '_hello',
  version: 1,
  meta: {
    title: 'Hello widget',
    description: 'The simplest possible widget — renders one line through the widget runtime.',
    answerProducing: false,
  },
  render: ({ mount, config }) => {
    const p = document.createElement('p');
    const kind = (config as { kind?: unknown }).kind ?? '_hello';
    p.textContent = 'Widget runtime alive · kind = ' + String(kind);
    p.style.margin = '0';
    p.style.fontSize = '15px';
    mount.appendChild(p);
  },
});
