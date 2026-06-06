/**
 * `thermo-piston` — the Class-11 Thermodynamics piston / First-Law widget.
 *
 * Re-implementation of the legacy Cabinet question `1/1/11/3/44/22`
 * (`openshiksha-cabinet/questions/raw/1/1/11/3/44/22.json`) on the IW-1
 * Widgets Framework. **Same physics, same visual story** — slider drives
 * heat supplied (ΔQ), up/down buttons drive piston motion (ΔW), the
 * formula readout shows ΔU = ΔQ − ΔW updating live.
 *
 * What changed from the legacy:
 *
 *   - **No jQuery, no jQuery-UI, no Bootstrap glyphicons.** Vanilla DOM +
 *     SVG inside the sandbox. The runtime that wraps this render function
 *     (`_sdk/runtime.ts`) only ships ~1 KB of plumbing — the savings
 *     compared to the legacy ~280 KB vendor head are real.
 *   - **Image assets dropped from the first pass.** The legacy widget
 *     referenced `8.gif` (gas molecules), `7.gif` (fire), `9.png` (ice)
 *     via Cabinet's `#{...}#` syntax. They make the visualisation nicer
 *     but are not the physics; flat colour blocks render correctly with
 *     zero asset fetching. Future IW-6 polish can re-add them via the
 *     `imageBase` SDK hook.
 *   - **Explanatory, not answer-producing.** The widget never calls
 *     `reportValue`. The student's answer to the question (ΔU for the
 *     specific `k`/`j` the question asks) is typed into the numeric
 *     answer field below the widget — exactly as in the legacy flow.
 *
 * Variables `k` and `j` arrive via `ctx.variables` (per-student sampled
 * by the croupier). The widget surfaces them in a "your question values"
 * note so the student can compare what the simulation does to what the
 * question asks for, without us having to thread a second `<RichContent>`
 * outside the sandbox.
 */

import { defineWidget } from '../_sdk/defineWidget';

interface ThermoConfig {
  /** Lower bound of the heat slider in Joules. Default −200. */
  heatMin?: number;
  /** Upper bound of the heat slider in Joules. Default +200. */
  heatMax?: number;
  /** Per-click increment of the piston work buttons in Joules. Default 5. */
  workStep?: number;
  /** Absolute bound for piston work in Joules. Default 200. */
  workMax?: number;
  /** Optional title shown above the simulation. */
  title?: string;
  /** Legacy compatibility — was set by PR #212; unused but accepted so old configs don't 400 the renderer. */
  initialVolume?: unknown;
  /** Legacy compatibility — was set by PR #212; unused. */
  maxHeat?: unknown;
}

export default defineWidget({
  kind: 'thermo-piston',
  version: 1,
  meta: {
    title: 'Thermodynamics — piston & First Law',
    description:
      'Drag the heat slider and pump the piston to feel ΔU = ΔQ − ΔW. ' +
      'Explanatory; the student types the numeric answer separately.',
    answerProducing: false,
  },
  render: (ctx) => {
    // Defaults mirror the legacy slider's `min:-200, max:200` and the
    // piston's ~200 px of vertical travel. workStep=5 keeps the click
    // responsive without making the piston jump visibly per press.
    const cfg = ctx.config as ThermoConfig;
    const heatMin = Number.isFinite(cfg.heatMin) ? (cfg.heatMin as number) : -200;
    const heatMax = Number.isFinite(cfg.heatMax) ? (cfg.heatMax as number) : 200;
    const workMax = Number.isFinite(cfg.workMax) ? (cfg.workMax as number) : 200;
    const workStep = Number.isFinite(cfg.workStep) ? (cfg.workStep as number) : 5;
    const title = typeof cfg.title === 'string' ? cfg.title : 'Thermodynamics — piston & First Law';

    // Inline style scoped to the widget root. The runtime's body already
    // has brand tokens (#FF6F00 brand, paper background, Inter+Fraunces);
    // we only set rules specific to this widget's layout.
    const style = document.createElement('style');
    style.textContent = `
      .tp-root { display: grid; gap: 12px; }
      .tp-title { font-family: "Fraunces", Georgia, serif; font-size: 18px; font-weight: 600; margin: 0; }
      .tp-stage { display: grid; grid-template-columns: 200px 1fr; gap: 14px; align-items: start; }
      .tp-controls { display: grid; gap: 10px; font-size: 14px; }
      .tp-formula { font-size: 16px; line-height: 1.55; }
      .tp-formula .tp-q { color: #B91C1C; font-weight: 600; }
      .tp-formula .tp-w { color: #1D4ED8; font-weight: 600; }
      .tp-formula .tp-u { color: #047857; font-weight: 700; }
      .tp-row { display: flex; flex-direction: column; gap: 4px; }
      .tp-slider { width: 100%; accent-color: #FF6F00; }
      .tp-btn {
        appearance: none; border: 1px solid #1B1A17; background: #fff;
        padding: 6px 10px; border-radius: 8px; font-family: inherit;
        cursor: pointer; font-size: 14px; min-width: 80px;
      }
      .tp-btn:hover { background: #FFF4E5; }
      .tp-btn:active { background: #FFE5C4; }
      .tp-btn-group { display: flex; gap: 6px; }
      .tp-vars { font-size: 13px; color: #4B463E; margin: 0; }
      .tp-reset { font-size: 12px; color: #4B463E; background: transparent; border: 0; cursor: pointer; text-decoration: underline; padding: 0; }
    `;
    ctx.mount.appendChild(style);

    const root = document.createElement('div');
    root.className = 'tp-root';
    ctx.mount.appendChild(root);

    const titleEl = document.createElement('p');
    titleEl.className = 'tp-title';
    titleEl.textContent = title;
    root.appendChild(titleEl);

    // SVG stage — the piston cylinder + a hot/cold zone strip below.
    const stage = document.createElement('div');
    stage.className = 'tp-stage';
    root.appendChild(stage);

    const SVG_NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(SVG_NS, 'svg');
    // viewBox: y=0 at the very top of the rod, cylinder opening at y=40,
    // cylinder bottom at y=250, heat strip down to y=300. The 40 px above
    // the cylinder is *where the rod sticks out* when the piston is high
    // — it is not blank padding, so we keep it tight.
    svg.setAttribute('viewBox', '0 0 200 300');
    svg.setAttribute('width', '180');
    svg.setAttribute('height', '270');
    svg.setAttribute('aria-label', 'Piston cylinder with heat source');

    // Cylinder walls (open at top).
    const wallL = document.createElementNS(SVG_NS, 'line');
    wallL.setAttribute('x1', '40');
    wallL.setAttribute('y1', '40');
    wallL.setAttribute('x2', '40');
    wallL.setAttribute('y2', '250');
    wallL.setAttribute('stroke', '#1B1A17');
    wallL.setAttribute('stroke-width', '4');
    svg.appendChild(wallL);

    const wallR = document.createElementNS(SVG_NS, 'line');
    wallR.setAttribute('x1', '160');
    wallR.setAttribute('y1', '40');
    wallR.setAttribute('x2', '160');
    wallR.setAttribute('y2', '250');
    wallR.setAttribute('stroke', '#1B1A17');
    wallR.setAttribute('stroke-width', '4');
    svg.appendChild(wallR);

    const wallB = document.createElementNS(SVG_NS, 'line');
    wallB.setAttribute('x1', '40');
    wallB.setAttribute('y1', '250');
    wallB.setAttribute('x2', '160');
    wallB.setAttribute('y2', '250');
    wallB.setAttribute('stroke', '#1B1A17');
    wallB.setAttribute('stroke-width', '4');
    svg.appendChild(wallB);

    // Gas (warm tint, height shrinks as piston comes down).
    const gas = document.createElementNS(SVG_NS, 'rect');
    gas.setAttribute('x', '42');
    gas.setAttribute('width', '116');
    gas.setAttribute('fill', '#FFD9A8');
    svg.appendChild(gas);

    // Gas particles — kinetic-theory style. Rest positions are sampled once
    // in a normalised [0,1]² grid inside the cylinder; on every animation
    // frame we offset each one by a sinusoidal jitter whose amplitude scales
    // with internal energy ΔU = ΔQ − ΔW (a proxy for temperature). Hot gas
    // → big amplitude / fast oscillation; cold gas → barely a wiggle.
    // Cylinder interior x range is roughly [44, 156] (4 px inside the walls).
    const PARTICLE_COUNT = 16;
    const particles: Array<{
      el: SVGCircleElement;
      rx: number; // 0..1 across cylinder width
      ry: number; // 0..1 across gas height
      phaseX: number;
      phaseY: number;
    }> = [];
    // Deterministic pseudo-random so the layout is stable across renders
    // (and so screenshots / visual baselines are reproducible).
    let seed = 1;
    const rand = () => {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    };
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const el = document.createElementNS(SVG_NS, 'circle');
      el.setAttribute('r', '3');
      el.setAttribute('fill', '#A03A00');
      el.setAttribute('opacity', '0.85');
      svg.appendChild(el);
      particles.push({
        el,
        rx: 0.05 + rand() * 0.9,
        ry: 0.05 + rand() * 0.9,
        phaseX: rand() * Math.PI * 2,
        phaseY: rand() * Math.PI * 2,
      });
    }

    // Piston (slab + rod). The slab is a fixed 14 px slice that slides
    // vertically. The rod is a slim **fixed-length** rectangle whose
    // bottom edge stays glued to the top of the slab — it shouldn't
    // grow/shrink as the piston moves; it just translates with it. (The
    // previous build sized the rod from `pistonY`, which meant it
    // ballooned wider/taller on compression and clipped through the gas.)
    const piston = document.createElementNS(SVG_NS, 'rect');
    piston.setAttribute('x', '40');
    piston.setAttribute('width', '120');
    piston.setAttribute('height', '14');
    piston.setAttribute('fill', '#4B463E');
    svg.appendChild(piston);

    const ROD_WIDTH = 6;
    const ROD_HEIGHT = 36; // fixed; rod just translates with the piston
    const rod = document.createElementNS(SVG_NS, 'rect');
    rod.setAttribute('x', String(100 - ROD_WIDTH / 2));
    rod.setAttribute('width', String(ROD_WIDTH));
    rod.setAttribute('height', String(ROD_HEIGHT));
    rod.setAttribute('fill', '#4B463E');
    svg.appendChild(rod);

    // Heat zone strip below — colour shifts red ↔ blue with sign of Q,
    // and a stylised flame / snowflake glyph fades in to echo the legacy
    // widget's `7.gif` (fire) / `9.png` (ice) sprite swap. Drawing the
    // glyphs **inline as SVG** keeps the widget self-contained: the
    // sandbox is opaque-origin, so a raster fetch from the app would add
    // a network round-trip + CORS surface for no real visual gain.
    const heatStrip = document.createElementNS(SVG_NS, 'rect');
    heatStrip.setAttribute('x', '40');
    heatStrip.setAttribute('y', '260');
    heatStrip.setAttribute('width', '120');
    heatStrip.setAttribute('height', '36');
    heatStrip.setAttribute('rx', '4');
    heatStrip.setAttribute('fill', '#E7E2D3');
    svg.appendChild(heatStrip);

    // Flame icon — a soft teardrop with an inner highlight. Sits on the
    // left of the heat strip when Q > 0. Width ≈ 22 px so it doesn't
    // crowd the label text.
    const fireGroup = document.createElementNS(SVG_NS, 'g');
    fireGroup.setAttribute('opacity', '0');
    const fireOuter = document.createElementNS(SVG_NS, 'path');
    fireOuter.setAttribute(
      'd',
      // M start near base, curl up on the left, peak with a small kick to
      // the right (the "tongue"), then come back down — a stylised flame.
      'M55 290 Q47 281 50 272 Q55 263 58 270 Q60 263 62 267 Q66 257 65 270 Q70 277 67 285 Q63 293 55 290 Z',
    );
    fireOuter.setAttribute('fill', '#F97316');
    const fireInner = document.createElementNS(SVG_NS, 'path');
    fireInner.setAttribute('d', 'M58 288 Q54 281 57 275 Q60 270 61 277 Q64 281 62 285 Q60 290 58 288 Z');
    fireInner.setAttribute('fill', '#FDE68A');
    fireGroup.appendChild(fireOuter);
    fireGroup.appendChild(fireInner);
    svg.appendChild(fireGroup);

    // Snowflake icon — six-fold radial of short lines with end-tick branches.
    // Sits on the left of the heat strip when Q < 0. Centred at (58, 278).
    const iceGroup = document.createElementNS(SVG_NS, 'g');
    iceGroup.setAttribute('opacity', '0');
    iceGroup.setAttribute('stroke', '#3B82F6');
    iceGroup.setAttribute('stroke-width', '1.4');
    iceGroup.setAttribute('stroke-linecap', 'round');
    const iceCx = 58;
    const iceCy = 278;
    const armLen = 9;
    const branchLen = 3;
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 3) * i;
      const ex = iceCx + Math.cos(a) * armLen;
      const ey = iceCy + Math.sin(a) * armLen;
      const arm = document.createElementNS(SVG_NS, 'line');
      arm.setAttribute('x1', String(iceCx));
      arm.setAttribute('y1', String(iceCy));
      arm.setAttribute('x2', String(ex));
      arm.setAttribute('y2', String(ey));
      iceGroup.appendChild(arm);
      // Two angled branches partway along each arm — classic snowflake.
      for (const sign of [-1, 1] as const) {
        const mx = iceCx + Math.cos(a) * (armLen * 0.55);
        const my = iceCy + Math.sin(a) * (armLen * 0.55);
        const ba = a + sign * (Math.PI / 3);
        const bx = mx + Math.cos(ba) * branchLen;
        const by = my + Math.sin(ba) * branchLen;
        const branch = document.createElementNS(SVG_NS, 'line');
        branch.setAttribute('x1', String(mx));
        branch.setAttribute('y1', String(my));
        branch.setAttribute('x2', String(bx));
        branch.setAttribute('y2', String(by));
        iceGroup.appendChild(branch);
      }
    }
    svg.appendChild(iceGroup);

    const heatLabel = document.createElementNS(SVG_NS, 'text');
    heatLabel.setAttribute('x', '108'); // shifted right so it doesn't overlap the icon
    heatLabel.setAttribute('y', '283');
    heatLabel.setAttribute('text-anchor', 'middle');
    heatLabel.setAttribute('font-size', '13');
    heatLabel.setAttribute('fill', '#1B1A17');
    heatLabel.textContent = 'no heat flow';
    svg.appendChild(heatLabel);

    stage.appendChild(svg);

    // Controls + formula panel.
    const right = document.createElement('div');
    right.className = 'tp-controls';
    stage.appendChild(right);

    // Heat row.
    const heatRow = document.createElement('div');
    heatRow.className = 'tp-row';
    const heatLabelEl = document.createElement('label');
    heatLabelEl.textContent = 'Heat supplied (ΔQ)';
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.className = 'tp-slider';
    slider.min = String(heatMin);
    slider.max = String(heatMax);
    slider.step = '1';
    slider.value = '0';
    slider.setAttribute('aria-label', 'Heat supplied to the system');
    heatRow.appendChild(heatLabelEl);
    heatRow.appendChild(slider);
    right.appendChild(heatRow);

    // Work row.
    const workRow = document.createElement('div');
    workRow.className = 'tp-row';
    const workLabel = document.createElement('label');
    workLabel.textContent = 'Piston · work done by gas (ΔW)';
    const btnGroup = document.createElement('div');
    btnGroup.className = 'tp-btn-group';
    const btnUp = document.createElement('button');
    btnUp.type = 'button';
    btnUp.className = 'tp-btn';
    btnUp.textContent = '▲ expand';
    const btnDown = document.createElement('button');
    btnDown.type = 'button';
    btnDown.className = 'tp-btn';
    btnDown.textContent = '▼ compress';
    btnGroup.appendChild(btnUp);
    btnGroup.appendChild(btnDown);
    workRow.appendChild(workLabel);
    workRow.appendChild(btnGroup);
    right.appendChild(workRow);

    // Reset.
    const resetBtn = document.createElement('button');
    resetBtn.type = 'button';
    resetBtn.className = 'tp-reset';
    resetBtn.textContent = 'reset to ΔQ = ΔW = 0';
    right.appendChild(resetBtn);

    // Formula readout.
    const formula = document.createElement('div');
    formula.className = 'tp-formula';
    formula.innerHTML =
      '<strong>ΔU = ΔQ − ΔW</strong><br>' +
      '= <span class="tp-q">0 J</span> − <span class="tp-w">0 J</span><br>' +
      '= <span class="tp-u">0 J</span>';
    right.appendChild(formula);

    // Variable hint — show k/j to the student so the simulation values
    // and the question values stay correlated in the same eye-line.
    const vars = ctx.variables;
    const k = vars && typeof vars.k !== 'undefined' ? vars.k : null;
    const j = vars && typeof vars.j !== 'undefined' ? vars.j : null;
    if (k !== null || j !== null) {
      const note = document.createElement('p');
      note.className = 'tp-vars';
      note.textContent =
        'Your question uses' +
        (k !== null ? ' k = ' + String(k) : '') +
        (k !== null && j !== null ? ',' : '') +
        (j !== null ? ' j = ' + String(j) : '') +
        '. Try matching those values in the controls above to feel the physics.';
      right.appendChild(note);
    }

    // State + render-update plumbing.
    let q = 0;
    let w = 0;
    // Current gas region in SVG coords. Updated by `paint()` so the rAF
    // animation loop knows where to put the particles even after a
    // compress/expand event has just resized the gas rectangle.
    let gasX = 44;
    let gasW = 112;
    let gasY = 74;
    let gasH = 176;
    let energyAmplitude = 1; // px of jitter; updated by paint() from u = q - w.
    const qSpan = formula.querySelector('.tp-q') as HTMLElement;
    const wSpan = formula.querySelector('.tp-w') as HTMLElement;
    const uSpan = formula.querySelector('.tp-u') as HTMLElement;

    function paint() {
      qSpan.textContent = String(q) + ' J';
      wSpan.textContent = String(w) + ' J';
      uSpan.textContent = String(q - w) + ' J';

      // Piston Y: 0 work → piston sits at gas-top (y = 60). Positive work
      // (expansion) → piston rises (smaller y). Negative work
      // (compression) → piston falls. Map work ∈ [−workMax, +workMax] to
      // ±(workMax visual units).
      const baseY = 60;
      const range = Math.min(140, workMax); // visual cap so piston stays inside cylinder
      // PISTON_Y_MIN keeps the slab inside the cylinder opening; PISTON_Y_MAX
      // leaves a hard floor of ~36 px of gas room so the gas never collapses
      // under the piston and the particles always have somewhere to jiggle.
      // The cylinder bottom (wall) sits at y = 250.
      const PISTON_Y_MIN = 40;
      const PISTON_Y_MAX = 200;
      const pistonY = Math.max(PISTON_Y_MIN, Math.min(PISTON_Y_MAX, baseY - (w / workMax) * range));
      piston.setAttribute('y', String(pistonY));
      // Rod's BOTTOM edge sits on the top of the piston slab; height is the
      // fixed `ROD_HEIGHT` constant so it doesn't change size as the piston
      // moves. Only its `y` translates.
      rod.setAttribute('y', String(pistonY - ROD_HEIGHT));
      // Gas region: starts below the slab, ends at the cylinder floor (250).
      gasX = 44;
      gasW = 112;
      gasY = pistonY + 14;
      gasH = Math.max(36, 250 - gasY); // matches the PISTON_Y_MAX floor above
      gas.setAttribute('x', String(gasX));
      gas.setAttribute('width', String(gasW));
      gas.setAttribute('y', String(gasY));
      gas.setAttribute('height', String(gasH));

      // Internal-energy drives particle vibration amplitude (kinetic-theory
      // intuition: T ∝ ⟨KE⟩, so the jiggle gets bigger when ΔU goes up).
      // ΔU = ΔQ − ΔW, normalised against the slider's full ±200 J range.
      // Baseline 1 px so even at U=0 the gas isn't a frozen lattice; cap at
      // 6 px so particles never escape the gas region's 36 px floor.
      const u = q - w;
      const norm = Math.max(-1, Math.min(1, u / 200));
      energyAmplitude = Math.max(0.4, Math.min(6, 1 + norm * 4));

      // Heat strip — red for Q>0, blue for Q<0, neutral for 0. The flame
      // / snowflake icons fade in proportionally to |Q| so a tiny nudge on
      // the slider gives a tiny glyph and a full swing gives a full one.
      let fill = '#E7E2D3';
      let label = 'no heat flow';
      let fireOpacity = 0;
      let iceOpacity = 0;
      if (q > 0) {
        fill = '#FCA5A5';
        label = 'heat in (warming)';
        fireOpacity = Math.min(1, q / 100);
      } else if (q < 0) {
        fill = '#93C5FD';
        label = 'heat out (cooling)';
        iceOpacity = Math.min(1, -q / 100);
      }
      heatStrip.setAttribute('fill', fill);
      heatLabel.textContent = label;
      fireGroup.setAttribute('opacity', fireOpacity.toFixed(2));
      iceGroup.setAttribute('opacity', iceOpacity.toFixed(2));
    }
    paint();

    // Particle animation loop. We use `requestAnimationFrame` rather than
    // `setInterval` so the browser pauses the loop when the iframe is
    // hidden (battery-friendly). Each particle's rest position is its
    // (rx, ry) inside the *current* gas region; the sinusoidal offset is
    // scaled by `energyAmplitude` (set by paint() above). Particle radius
    // also breathes lightly so the speed change reads visually even when
    // the gas is compressed and amplitude has less room to grow.
    let startTime = 0;
    function tick(now: number) {
      if (!startTime) startTime = now;
      const t = (now - startTime) / 1000; // seconds
      const speed = 2 + energyAmplitude * 1.4; // rad/s — scales with energy
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        const baseX = gasX + p.rx * gasW;
        const baseY = gasY + p.ry * gasH;
        const dx = Math.sin(t * speed + p.phaseX) * energyAmplitude;
        const dy = Math.cos(t * speed * 0.9 + p.phaseY) * energyAmplitude;
        const cx = Math.max(gasX + 3, Math.min(gasX + gasW - 3, baseX + dx));
        const cy = Math.max(gasY + 3, Math.min(gasY + gasH - 3, baseY + dy));
        p.el.setAttribute('cx', String(cx));
        p.el.setAttribute('cy', String(cy));
        // Radius pulses a little (2.4 → 3.6 px) so hot gas reads as more
        // energetic than just "moves further". Cold gas calms visibly.
        const r = 2.4 + (energyAmplitude / 6) * 1.2;
        p.el.setAttribute('r', r.toFixed(2));
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);

    slider.addEventListener('input', () => {
      q = parseInt(slider.value, 10) || 0;
      paint();
    });
    // No `ctx.requestResize()` here on purpose — the SVG is a fixed
    // 180×270 box, so the iframe content size doesn't change when the
    // piston moves. Calling requestResize would re-post a `resize`
    // message whose value can drift by a pixel against the host's `+4`
    // buffer, ratcheting the iframe height a pixel taller on every
    // click. The runtime's ResizeObserver still catches any *real*
    // content-size change.
    btnUp.addEventListener('click', () => {
      w = Math.min(workMax, w + workStep);
      paint();
    });
    btnDown.addEventListener('click', () => {
      w = Math.max(-workMax, w - workStep);
      paint();
    });
    resetBtn.addEventListener('click', () => {
      q = 0;
      w = 0;
      slider.value = '0';
      paint();
    });
  },
});
