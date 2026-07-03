import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Badge, Card, Input, Select, Textarea } from '@/shared/ui';
import { InteractiveWidget } from '@/shared/ui/InteractiveWidget';
import { widgetRegistry, type WidgetKind } from '@/widgets/registry';
import type { WidgetModule, WidgetParamsSchema } from '@/widgets/_sdk/defineWidget';
import { StepHintPanel } from './StepHintPanel';
import { PracticeProblemPanel } from './PracticeProblemPanel';

const WIDGET_KINDS = Object.keys(widgetRegistry).sort() as WidgetKind[];

const CUSTOM_HTML_DEMO = String.raw`<section class="os-demo">
  <style>
    .os-demo {
      --brand: #ff6f00;
      --ink: #172033;
      --paper: #fffaf2;
      margin: 0;
      padding: 20px;
      border-radius: 18px;
      background:
        radial-gradient(circle at 20% 20%, rgba(255, 111, 0, 0.18), transparent 28%),
        linear-gradient(135deg, #fffaf2, #ffffff);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
      overflow: hidden;
    }
    .os-demo h2 {
      margin: 0 0 6px;
      font-size: 24px;
      line-height: 1.1;
    }
    .os-demo p {
      margin: 0;
      color: #526070;
    }
    .os-demo-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 170px;
      gap: 18px;
      align-items: center;
      margin-top: 18px;
    }
    .os-demo-card {
      border: 1px solid rgba(23, 32, 51, 0.1);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.78);
      padding: 14px;
      box-shadow: 0 16px 45px rgba(23, 32, 51, 0.1);
    }
    .os-orbit {
      position: relative;
      height: 150px;
      border-radius: 18px;
      background: linear-gradient(180deg, #19253a, #243b57);
      overflow: hidden;
    }
    .os-orbit::before {
      content: "";
      position: absolute;
      inset: 24px;
      border: 1px dashed rgba(255, 255, 255, 0.35);
      border-radius: 999px;
    }
    .os-planet {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 42px;
      height: 42px;
      border-radius: 999px;
      background: var(--brand);
      box-shadow: 0 0 28px rgba(255, 111, 0, 0.72);
      transform: translate(-50%, -50%);
    }
    .os-satellite {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 16px;
      height: 16px;
      border-radius: 999px;
      background: #8ee3ff;
      transform: rotate(var(--angle, 0deg)) translateX(var(--radius, 56px));
      transform-origin: 0 0;
      box-shadow: 0 0 18px rgba(142, 227, 255, 0.9);
    }
    .os-demo label {
      display: block;
      margin-bottom: 8px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #7c8794;
    }
    .os-demo input[type="range"] {
      width: 100%;
      accent-color: var(--brand);
    }
    .os-readout {
      margin-top: 12px;
      font-size: 34px;
      font-weight: 800;
      color: var(--brand);
    }
    @media (max-width: 560px) {
      .os-demo-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>

  <h2>Sandboxed HTML can still feel alive</h2>
  <p>Inline CSS and JavaScript run inside the widget iframe, isolated from the app.</p>

  <div class="os-demo-grid">
    <div class="os-demo-card">
      <label for="energy">Energy level</label>
      <input id="energy" type="range" min="1" max="10" value="6" />
      <div class="os-readout"><span id="energy-value">6</span>x</div>
      <p id="energy-copy">Move the slider to resize the orbit.</p>
    </div>

    <div class="os-orbit" aria-label="Animated orbit preview">
      <div class="os-planet"></div>
      <div class="os-satellite" id="satellite"></div>
    </div>
  </div>

  <script>
    (function () {
      var slider = document.getElementById('energy');
      var value = document.getElementById('energy-value');
      var satellite = document.getElementById('satellite');
      var copy = document.getElementById('energy-copy');
      var angle = 0;

      function update() {
        var energy = Number(slider.value);
        value.textContent = String(energy);
        satellite.style.setProperty('--radius', 38 + energy * 7 + 'px');
        copy.textContent = energy >= 8
          ? 'High energy: fast, wide motion.'
          : energy <= 3
            ? 'Low energy: calm, close motion.'
            : 'Balanced energy: steady motion.';
      }

      slider.addEventListener('input', update);
      update();

      function tick() {
        angle = (angle + Number(slider.value)) % 360;
        satellite.style.setProperty('--angle', angle + 'deg');
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    })();
  </script>
</section>`;

const CUSTOM_DEFAULT_CONFIG: Partial<Record<WidgetKind, Record<string, unknown>>> = {
  'custom-html': { html: CUSTOM_HTML_DEMO },
};

function defaultConfigFromSchema(schema: WidgetParamsSchema | undefined): Record<string, unknown> {
  const properties = schema?.properties;
  if (!properties || typeof properties !== 'object' || Array.isArray(properties)) return {};

  return Object.fromEntries(
    Object.entries(properties as Record<string, unknown>).flatMap(([key, value]) => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return [];
      const prop = value as { default?: unknown; type?: unknown; enum?: unknown };
      if ('default' in prop) return [[key, prop.default]];
      if (Array.isArray(prop.enum) && prop.enum.length > 0) return [[key, prop.enum[0]]];
      if (prop.type === 'number' || prop.type === 'integer') return [[key, 0]];
      if (prop.type === 'boolean') return [[key, false]];
      if (prop.type === 'string') return [[key, '']];
      return [];
    }),
  );
}

function prettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function parseJsonObject(source: string): { value: Record<string, unknown>; error: null } | { value: null; error: string } {
  try {
    const parsed = JSON.parse(source);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return { value: null, error: 'JSON must be an object.' };
    }
    return { value: parsed as Record<string, unknown>, error: null };
  } catch (err) {
    return { value: null, error: err instanceof Error ? err.message : String(err) };
  }
}

function initialKind(searchKind: string | null): WidgetKind {
  return WIDGET_KINDS.includes(searchKind as WidgetKind) ? (searchKind as WidgetKind) : 'thermo-piston';
}

function defaultConfigForKind(kind: WidgetKind): Record<string, unknown> {
  return CUSTOM_DEFAULT_CONFIG[kind] ?? defaultConfigFromSchema(widgetRegistry[kind].paramsSchema);
}

export function WidgetDevPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [kind, setKind] = useState<WidgetKind>(() => initialKind(searchParams.get('kind')));
  const [configText, setConfigText] = useState(() => prettyJson(defaultConfigForKind(kind)));
  const [variablesText, setVariablesText] = useState('{}');
  const [lastValue, setLastValue] = useState<unknown>(undefined);
  // GSV-4 step-coach explorer (only shown for the `step-solver` widget): a
  // previous/current line pair fed to the host-side AI wrong-step explainer.
  const [coachPrev, setCoachPrev] = useState('2x + 3 = 7');
  const [coachCur, setCoachCur] = useState('2x = 10');
  // GSV-4b: where the current coach pair came from. A wrong step *committed in
  // the widget* auto-feeds the pair (`'widget'`); typing in the inputs below
  // switches back to `'manual'`. Purely a UI affordance — the deterministic
  // verdict still decides everything.
  const [coachSource, setCoachSource] = useState<'manual' | 'widget'>('manual');

  const widget: WidgetModule = widgetRegistry[kind];
  const configState = useMemo(() => parseJsonObject(configText), [configText]);
  const variableState = useMemo(() => parseJsonObject(variablesText), [variablesText]);
  const canPreview = !configState.error && !variableState.error;
  const previewConfig = configState.value ?? {};
  const previewVariables = (variableState.value ?? {}) as Record<string, number | string | boolean>;

  const selectKind = (next: WidgetKind) => {
    setKind(next);
    setConfigText(prettyJson(defaultConfigForKind(next)));
    setLastValue(undefined);
    setSearchParams({ kind: next }, { replace: true });
  };

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-ink-100 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-7">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-700">
            Interactive Widgets
          </p>
          <h1 className="font-display text-3xl font-semibold text-ink-900">Widget dev playground</h1>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-5 px-6 py-6 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <Card className="space-y-4">
            <Select
              label="Widget kind"
              value={kind}
              onChange={(event) => selectKind(event.target.value as WidgetKind)}
            >
              {WIDGET_KINDS.map((candidate) => (
                <option key={candidate} value={candidate}>
                  {candidate}
                </option>
              ))}
            </Select>

            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={widget.meta.answerProducing ? 'attention' : 'neutral'}>
                  {widget.meta.answerProducing ? 'answer-producing' : 'explanatory'}
                </Badge>
                <Badge tone="brand">v{widget.version}</Badge>
              </div>
              <h2 className="font-display text-xl font-semibold text-ink-900">{widget.meta.title}</h2>
              {widget.meta.description && <p className="text-sm text-ink-600">{widget.meta.description}</p>}
            </div>
          </Card>

          <Card className="space-y-4">
            <Textarea
              label="Config JSON"
              value={configText}
              rows={14}
              spellCheck={false}
              className="font-mono text-sm"
              error={configState.error}
              onChange={(event) => setConfigText(event.target.value)}
            />
            <Textarea
              label="Variables JSON"
              value={variablesText}
              rows={6}
              spellCheck={false}
              className="font-mono text-sm"
              error={variableState.error}
              onChange={(event) => setVariablesText(event.target.value)}
            />
          </Card>
        </aside>

        <section className="space-y-4">
          <Card>
            {canPreview ? (
              <InteractiveWidget
                key={`${kind}:${configText}:${variablesText}`}
                kind={kind}
                config={previewConfig}
                variables={previewVariables}
                minHeight={260}
                onValue={setLastValue}
                onStep={(step) => {
                  // GSV-4b auto-feed: a wrong step committed in the widget feeds
                  // its exact line pair to the coach below — no copy-paste. Only
                  // 'bad' steps are coachable (the AI never explains a correct or
                  // unparseable line).
                  if (step.verdict === 'bad') {
                    setCoachPrev(step.previous);
                    setCoachCur(step.current);
                    setCoachSource('widget');
                  }
                }}
              />
            ) : (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
                Fix the JSON error before previewing.
              </div>
            )}
          </Card>

          <Card>
            <p className="text-xs font-semibold uppercase tracking-widest text-ink-400">Last reported value</p>
            <pre className="mt-2 overflow-auto rounded-lg bg-ink-900 p-3 text-sm text-white">
              {lastValue === undefined ? 'No value reported yet.' : prettyJson(lastValue)}
            </pre>
          </Card>

          {kind === 'step-solver' && (
            <Card className="space-y-4">
              <div>
                <h2 className="font-display text-lg font-semibold text-ink-900">Wrong-step explainer</h2>
                <p className="mt-1 text-sm text-ink-600">
                  The deterministic engine decides ✓/✗ in the sandbox; this host-side coach asks the AI
                  to explain a step it has <em>already</em> judged wrong. AI never grades.
                </p>
              </div>
              {coachSource === 'widget' && (
                <p
                  className="rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm text-brand-800"
                  role="status"
                >
                  ⚡ Auto-filled from your last wrong step in the widget above.
                </p>
              )}
              <div className="grid gap-3">
                <Input
                  label="Previous line"
                  value={coachPrev}
                  spellCheck={false}
                  className="font-mono text-sm"
                  onChange={(event) => {
                    setCoachPrev(event.target.value);
                    setCoachSource('manual');
                  }}
                />
                <Input
                  label="New line"
                  value={coachCur}
                  spellCheck={false}
                  className="font-mono text-sm"
                  onChange={(event) => {
                    setCoachCur(event.target.value);
                    setCoachSource('manual');
                  }}
                />
              </div>
              <StepHintPanel previous={coachPrev} current={coachCur} />
            </Card>
          )}

          {/* PV-3: the propose-and-verify practice-problem generator. Always
              shown (it authors its own `number-line` problem, independent of the
              currently-selected preview kind); every proposal is verified
              answerable by PV-1 server-side before it renders here. */}
          <Card>
            <PracticeProblemPanel />
          </Card>
        </section>
      </main>
    </div>
  );
}
