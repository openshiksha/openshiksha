import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Badge, Card, InteractiveWidget, Select, Textarea } from '@/shared/ui';
import { widgetRegistry, type WidgetKind } from '@/widgets/registry';
import type { WidgetModule, WidgetParamsSchema } from '@/widgets/_sdk/defineWidget';

const WIDGET_KINDS = Object.keys(widgetRegistry).sort() as WidgetKind[];

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

export function WidgetDevPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [kind, setKind] = useState<WidgetKind>(() => initialKind(searchParams.get('kind')));
  const [configText, setConfigText] = useState(() => prettyJson(defaultConfigFromSchema(widgetRegistry[kind].paramsSchema)));
  const [variablesText, setVariablesText] = useState('{}');
  const [lastValue, setLastValue] = useState<unknown>(undefined);

  const widget: WidgetModule = widgetRegistry[kind];
  const configState = useMemo(() => parseJsonObject(configText), [configText]);
  const variableState = useMemo(() => parseJsonObject(variablesText), [variablesText]);
  const canPreview = !configState.error && !variableState.error;
  const previewConfig = configState.value ?? {};
  const previewVariables = (variableState.value ?? {}) as Record<string, number | string | boolean>;

  const selectKind = (next: WidgetKind) => {
    setKind(next);
    setConfigText(prettyJson(defaultConfigFromSchema(widgetRegistry[next].paramsSchema)));
    setLastValue(undefined);
    setSearchParams({ kind: next }, { replace: true });
  };

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-ink-100 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-7">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">
            Interactive Widgets · IW-8
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
        </section>
      </main>
    </div>
  );
}
