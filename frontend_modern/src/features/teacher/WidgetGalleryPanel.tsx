import { useMemo, useState } from 'react';
import { Card } from '@/shared/ui';
import { AIBadge } from '@/shared/ui/AIBadge';
import { InteractiveWidget } from '@/shared/ui/InteractiveWidget';
import { useT } from '@/shared/i18n';
import { widgetRegistry } from '@/widgets/registry';
import type { WidgetModule } from '@/widgets/_sdk/defineWidget';
import { useWidgetAuthoring } from './useWidgetAuthoring';

/**
 * Tier-1 "Configure" authoring surface — the teacher gallery for the
 * Interactive Widgets Framework (IW-5).
 *
 * Lists every registered widget kind that's user-facing, lets the teacher
 * pick one, auto-generates a config form from the kind's
 * `params.schema.json`, and shows a **live preview** that re-renders on
 * every config change. When the teacher clicks "Use this widget", we
 * surface the chosen `{ kind, config }` to the parent (CreateQuestionPage)
 * which stamps `widget_kind` + `widget_config` on the active subpart.
 *
 * Describe-to-Build (DTB-3)
 * -------------------------
 * The grid view also carries a plain-English prompt box: the teacher
 * types "a number line where students mark 3/4", we POST it to the
 * teacher-only `/ai/widget-authoring/` endpoint, and the returned
 * `{widget_kind, widget_config}` proposal drops straight into the *same*
 * configure view (live preview + schema form) for editing before attach.
 * The proposal is schema-valid by construction on the backend (DTB-1
 * validation → DTB-2 clamp-repair → safe default), so the AI never emits
 * code and never touches the grader — it only authors config-as-data.
 * Provenance is honest via `AIBadge`; the no-key/timeout fallback returns
 * a deterministic safe default and shows a neutral `Auto-built` badge.
 *
 * Filtering rules
 * ---------------
 * - **Framework-internal kinds** (prefix `_`, e.g. `_hello`) are hidden.
 *   The teacher gallery never surfaces SDK plumbing.
 * - **`custom-html`** is hidden by default. It's the admin-only escape
 *   hatch (IW-7); regular teachers should not be attaching raw HTML
 *   widgets to questions. The school-admin UI is a future surface where
 *   this filter relaxes.
 *
 * Form-generation scope
 * ---------------------
 * The form covers the JSON-Schema property types Real Widgets™ use today:
 * `number`, `string`, `boolean`. Required fields render a red asterisk;
 * defaults pre-populate the input. Unknown property types fall through
 * to a JSON textarea so the teacher can still author them — clearly
 * marked so it's obvious this is the escape hatch.
 *
 * The preview iframe receives `variables = {}` because the gallery
 * doesn't yet know what `{{var}}` tokens the question will sample;
 * widgets that use `ctx.variables` (e.g. thermo-piston's "your question
 * values" hint) just show their fallback. IW-5 follow-up: pipe through
 * the draft's `variable_constraints` so the preview matches what the
 * student will see.
 */

type GalleryEntry = WidgetModule;

interface WidgetGalleryPanelProps {
  /** Currently-applied kind on the subpart, if any. */
  initialKind?: string;
  /** Currently-applied config on the subpart, if any. */
  initialConfig?: Record<string, unknown>;
  /** Called when the teacher clicks "Use this widget". */
  onApply: (selection: { kind: string; config: Record<string, unknown> }) => void;
  /** Called when the teacher clicks "Cancel" (closes the panel without applying). */
  onCancel: () => void;
}

interface SchemaProperty {
  type?: string;
  description?: string;
  default?: unknown;
  enum?: unknown[];
  deprecated?: boolean;
  exclusiveMinimum?: number;
  minimum?: number;
  maximum?: number;
}

interface ParamsSchema {
  properties?: Record<string, SchemaProperty>;
  required?: string[];
  description?: string;
}

const TEACHER_VISIBLE = (m: WidgetModule): boolean => {
  if (m.kind.startsWith('_')) return false; // framework-internal
  if (m.kind === 'custom-html') return false; // admin-only escape hatch
  return true;
};

function defaultConfigFromSchema(schema: ParamsSchema | undefined): Record<string, unknown> {
  if (!schema?.properties) return {};
  const out: Record<string, unknown> = {};
  for (const [name, prop] of Object.entries(schema.properties)) {
    if (prop.deprecated) continue;
    if (prop.default !== undefined) out[name] = prop.default;
  }
  return out;
}

function coerceValue(prop: SchemaProperty | undefined, raw: string): unknown {
  if (!prop) return raw;
  if (prop.type === 'number') {
    if (raw.trim() === '') return undefined;
    const n = Number(raw);
    return Number.isFinite(n) ? n : raw;
  }
  if (prop.type === 'boolean') return raw === 'true';
  return raw;
}

function PropertyField({
  name,
  prop,
  required,
  value,
  onChange,
}: {
  name: string;
  prop: SchemaProperty;
  required: boolean;
  value: unknown;
  onChange: (next: unknown) => void;
}) {
  const id = `wgf-${name}`;
  const description = prop.description ?? '';

  if (prop.type === 'boolean') {
    return (
      <label htmlFor={id} className="flex items-start gap-2 text-sm">
        <input
          id={id}
          type="checkbox"
          checked={value === true}
          onChange={(e) => onChange(e.target.checked)}
          className="mt-0.5 h-4 w-4 accent-brand-600"
        />
        <span>
          <span className="font-semibold text-ink-900">
            {name}
            {required && <span className="ml-1 text-red-600">*</span>}
          </span>
          {description && <span className="block text-xs text-ink-500">{description}</span>}
        </span>
      </label>
    );
  }

  // number + string + everything-else use the same labelled text input.
  const inputType = prop.type === 'number' ? 'number' : 'text';
  return (
    <label htmlFor={id} className="grid gap-1 text-sm">
      <span className="font-semibold text-ink-900">
        {name}
        {required && <span className="ml-1 text-red-600">*</span>}
      </span>
      <input
        id={id}
        type={inputType}
        value={value === undefined || value === null ? '' : String(value)}
        onChange={(e) => onChange(coerceValue(prop, e.target.value))}
        placeholder={prop.default !== undefined ? `default: ${String(prop.default)}` : undefined}
        className="rounded border border-ink-200 bg-paper px-2 py-1 focus:border-brand-600 focus:outline-none"
      />
      {description && <span className="text-xs text-ink-500">{description}</span>}
    </label>
  );
}

function ConfigForm({
  schema,
  config,
  onChange,
}: {
  schema: ParamsSchema | undefined;
  config: Record<string, unknown>;
  onChange: (next: Record<string, unknown>) => void;
}) {
  const t = useT();
  const properties = schema?.properties ?? {};
  const required = new Set(schema?.required ?? []);

  // No schema → expose the JSON textarea escape hatch so the teacher can
  // still author *something*, with a banner explaining what's going on.
  if (!schema || Object.keys(properties).length === 0) {
    return (
      <div className="grid gap-2">
        <p className="text-xs text-amber-700">
          {t('widgetGallery.noSchema')}
        </p>
        <textarea
          rows={8}
          value={JSON.stringify(config, null, 2)}
          onChange={(e) => {
            try {
              onChange(JSON.parse(e.target.value));
            } catch {
              /* leave config unchanged until the JSON parses */
            }
          }}
          className="rounded border border-ink-200 bg-paper px-2 py-1 font-mono text-xs"
        />
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {Object.entries(properties).map(([name, prop]) => {
        if (prop.deprecated) return null;
        return (
          <PropertyField
            key={name}
            name={name}
            prop={prop}
            required={required.has(name)}
            value={config[name]}
            onChange={(next) => {
              const updated = { ...config };
              if (next === undefined || next === '') delete updated[name];
              else updated[name] = next;
              onChange(updated);
            }}
          />
        );
      })}
    </div>
  );
}

export function WidgetGalleryPanel({
  initialKind,
  initialConfig,
  onApply,
  onCancel,
}: WidgetGalleryPanelProps) {
  const t = useT();
  const galleryEntries = useMemo<GalleryEntry[]>(
    () => Object.values(widgetRegistry).filter(TEACHER_VISIBLE),
    [],
  );

  // If the subpart already has a kind, preselect it so the teacher lands
  // on edit-mode rather than the gallery grid.
  const [selectedKind, setSelectedKind] = useState<string | undefined>(initialKind);
  const selected = selectedKind ? widgetRegistry[selectedKind as keyof typeof widgetRegistry] : undefined;
  const schema = selected?.paramsSchema as ParamsSchema | undefined;
  const [config, setConfig] = useState<Record<string, unknown>>(
    initialConfig ?? defaultConfigFromSchema(schema),
  );

  // ── DTB-3: Describe-to-Build ────────────────────────────────────────
  // Plain-English prompt → backend proposes a schema-valid {kind, config}.
  // We track the proposal's provenance so the configure view can wear an
  // honest badge (`✨ AI-generated` vs neutral `Auto-built`) and so the
  // deterministic-fallback path gets a friendly "AI unavailable" line.
  const [description, setDescription] = useState('');
  const [aiProvenance, setAiProvenance] = useState<
    { modelUsed: string; aiAvailable: boolean } | null
  >(null);
  const authoring = useWidgetAuthoring();

  const handleSelect = (kind: string) => {
    setSelectedKind(kind);
    // A manual gallery pick is never an AI proposal — clear any badge.
    setAiProvenance(null);
    // Fresh kind → reset config to its defaults so a previous kind's
    // fields don't leak into the preview.
    if (kind !== initialKind) {
      const next = widgetRegistry[kind as keyof typeof widgetRegistry];
      setConfig(defaultConfigFromSchema(next?.paramsSchema as ParamsSchema | undefined));
    } else {
      setConfig(initialConfig ?? defaultConfigFromSchema(schema));
    }
  };

  const handleGenerate = () => {
    const prompt = description.trim();
    if (!prompt || authoring.isPending) return;
    authoring.mutate(
      { description: prompt },
      {
        onSuccess: (res) => {
          // The backend guarantees a schema-valid config (DTB-1 validation →
          // DTB-2 clamp-repair → safe default), so we can drop it straight
          // into the live preview + schema form. Land the teacher in the
          // configure view with the proposal pre-loaded.
          setSelectedKind(res.widget_kind);
          setConfig(res.widget_config);
          setAiProvenance({ modelUsed: res.model_used, aiAvailable: res.ai_available });
        },
      },
    );
  };

  // ── Gallery grid (no kind selected) ─────────────────────────────────
  if (!selected) {
    return (
      <Card className="grid gap-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="font-display text-lg font-semibold text-ink-900">{t('widgetGallery.pickTitle')}</h3>
            <p className="text-sm text-ink-500">
              {t('widgetGallery.pickDesc')}
            </p>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="text-sm text-ink-500 hover:text-ink-900"
          >
            {t('common.cancel')}
          </button>
        </div>

        {/* ── DTB-3: Describe-to-Build prompt box ──────────────────── */}
        <div className="grid gap-2 rounded-xl border border-brand-200 bg-brand-50/60 p-3">
          <div className="flex items-center gap-2">
            <span aria-hidden className="text-base">✨</span>
            <h4 className="font-semibold text-ink-900">{t('widgetGallery.describeTitle')}</h4>
          </div>
          <p className="text-xs text-ink-500">{t('widgetGallery.describeDesc')}</p>
          <textarea
            aria-label={t('widgetGallery.describeTitle')}
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={t('widgetGallery.describePlaceholder')}
            className="rounded border border-ink-200 bg-paper px-2 py-1.5 text-sm focus:border-brand-600 focus:outline-none"
          />
          <div className="flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={authoring.isPending || description.trim() === ''}
              className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {authoring.isPending
                ? t('widgetGallery.describeGenerating')
                : t('widgetGallery.describeButton')}
            </button>
            <span className="text-[11px] uppercase tracking-wider text-ink-400">
              {t('widgetGallery.describeOrPick')}
            </span>
          </div>
          {authoring.isError && (
            <p role="alert" className="text-xs text-red-600">
              {t('widgetGallery.describeError')}
            </p>
          )}
        </div>

        {galleryEntries.length === 0 ? (
          <p className="text-sm text-ink-500 italic">{t('widgetGallery.noneRegistered')}</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {galleryEntries.map((entry) => (
              <button
                key={entry.kind}
                type="button"
                onClick={() => handleSelect(entry.kind)}
                className="rounded-xl border border-ink-200 bg-paper p-3 text-left hover:border-brand-600 hover:bg-brand-50"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-ink-900">{entry.meta.title}</h4>
                  {entry.meta.answerProducing && (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-900">
                      {t('widgetGallery.answerBadge')}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-ink-500">{entry.meta.description ?? ' '}</p>
                <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-ink-400">
                  {entry.kind} · v{entry.version}
                </p>
              </button>
            ))}
          </div>
        )}
      </Card>
    );
  }

  // ── Configure (kind selected, schema-driven form + preview) ─────────
  return (
    <Card className="grid gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-wider text-ink-400">
            {selected.kind} · v{selected.version}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-display text-lg font-semibold text-ink-900">{selected.meta.title}</h3>
            {/* DTB-3: honest provenance when this config came from the AI
                builder — `✨ AI-generated` for a real proposal, neutral
                `Auto-built` when the cascade fell back to a safe default. */}
            {aiProvenance && (
              <AIBadge
                modelUsed={aiProvenance.modelUsed}
                stubLabel={t('widgetGallery.aiStubLabel')}
              />
            )}
          </div>
          {selected.meta.description && (
            <p className="text-sm text-ink-500">{selected.meta.description}</p>
          )}
          {aiProvenance && !aiProvenance.aiAvailable && (
            <p className="mt-1 text-xs text-amber-700">{t('widgetGallery.describeFallback')}</p>
          )}
        </div>
        <button
          type="button"
          onClick={() => setSelectedKind(undefined)}
          className="text-sm text-ink-500 hover:text-ink-900"
        >
          {t('widgetGallery.backToGallery')}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">{t('widgetGallery.config')}</p>
          <ConfigForm schema={schema} config={config} onChange={setConfig} />
        </div>
        <div className="grid gap-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">{t('widgetGallery.preview')}</p>
          <InteractiveWidget
            kind={selected.kind}
            config={config}
            // IW-5 follow-up: pipe variable_constraints sampled values
            // through so widgets that read ctx.variables show realistic
            // numbers in the preview.
            variables={{}}
            minHeight={140}
          />
          <p className="text-[11px] text-ink-400">
            {t('widgetGallery.previewNote')}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-ink-100 pt-3">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-ink-200 px-3 py-1.5 text-sm hover:bg-ink-50"
        >
          {t('common.cancel')}
        </button>
        <button
          type="button"
          onClick={() => onApply({ kind: selected.kind, config })}
          className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700"
        >
          {t('widgetGallery.useThis')}
        </button>
      </div>
    </Card>
  );
}
