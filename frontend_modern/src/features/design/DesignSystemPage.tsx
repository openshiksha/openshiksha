import { Logo, Button, Card, Badge, RichContent, InteractiveWidget, Skeleton } from '@/shared/ui';

/**
 * Living catalogue of the V2 "Chalk & Unlock" design system. Every new `ui/`
 * primitive and token must show up here. This is how we keep the system visible
 * and prevent drift across sessions. See docs/initiatives/2026-design-system-v2.md.
 */
// Full class strings (Tailwind's JIT only detects complete literals, not `bg-brand-${n}`).
const BRAND_SCALE: Array<[string, string]> = [
  ['brand-50', 'bg-brand-50'],
  ['brand-100', 'bg-brand-100'],
  ['brand-200', 'bg-brand-200'],
  ['brand-300', 'bg-brand-300'],
  ['brand-400', 'bg-brand-400'],
  ['brand-500', 'bg-brand-500'],
  ['brand-600', 'bg-brand-600'],
  ['brand-700', 'bg-brand-700'],
  ['brand-800', 'bg-brand-800'],
  ['brand-900', 'bg-brand-900'],
];
const INK_SCALE: Array<[string, string]> = [
  ['ink-50', 'bg-ink-50'],
  ['ink-100', 'bg-ink-100'],
  ['ink-200', 'bg-ink-200'],
  ['ink-300', 'bg-ink-300'],
  ['ink-400', 'bg-ink-400'],
  ['ink-500', 'bg-ink-500'],
  ['ink-600', 'bg-ink-600'],
  ['ink-700', 'bg-ink-700'],
  ['ink-800', 'bg-ink-800'],
  ['ink-900', 'bg-ink-900'],
];

const Section = ({ title, kicker, children }: { title: string; kicker?: string; children: React.ReactNode }) => (
  <section className="animate-fade-up">
    <div className="mb-5">
      {kicker && <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">{kicker}</p>}
      <h2 className="font-display text-2xl font-semibold text-ink-900">{title}</h2>
    </div>
    {children}
  </section>
);

const Swatch = ({ name, className, dark }: { name: string; className: string; dark?: boolean }) => (
  <div className="overflow-hidden rounded-xl border border-ink-100">
    <div className={`h-14 ${className}`} />
    <div className={`px-2 py-1.5 text-[11px] font-medium ${dark ? 'text-white bg-ink-800' : 'text-ink-600 bg-white'}`}>
      {name}
    </div>
  </div>
);

export const DesignSystemPage = () => (
  <div className="bg-paper min-h-screen">
    {/* Hero — chalkboard heritage */}
    <header className="bg-chalkboard text-white">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <Logo size="lg" float wordmarkClassName="text-white" />
        <h1 className="mt-6 max-w-2xl font-display text-4xl font-semibold leading-tight text-balance">
          The “Chalk &amp; Unlock” design system
        </h1>
        <p className="mt-3 max-w-xl text-ink-200">
          Warm, branded, and intentional — professional enough for parents, a
          little fun for kids. Built from the legacy keyhole mark and a
          chalk-on-paper palette.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Badge tone="brand">brand #FF6F00</Badge>
          <Badge tone="neutral" className="!bg-white/10 !text-white">Fraunces + Inter</Badge>
          <Badge tone="neutral" className="!bg-white/10 !text-white">v2 · living catalogue</Badge>
        </div>
      </div>
    </header>

    <main className="mx-auto max-w-5xl space-y-14 px-6 py-12">
      <Section kicker="Foundation" title="Colour">
        <p className="mb-3 text-sm text-ink-500">Brand — the “unlock” colour. Anchor is <code>brand-600</code>.</p>
        <div className="grid grid-cols-5 gap-2 sm:grid-cols-10">
          {BRAND_SCALE.map(([name, cls]) => (
            <Swatch key={name} name={name} className={cls} />
          ))}
        </div>
        <p className="mb-3 mt-6 text-sm text-ink-500">Ink — warm chalkboard neutrals for text &amp; surfaces.</p>
        <div className="grid grid-cols-5 gap-2 sm:grid-cols-10">
          {INK_SCALE.map(([name, cls]) => (
            <Swatch key={name} name={name} className={cls} />
          ))}
        </div>
        <p className="mb-3 mt-6 text-sm text-ink-500">Semantic — success / attention / urgent.</p>
        <div className="grid grid-cols-3 gap-2">
          <Swatch name="success" className="bg-emerald-500" />
          <Swatch name="attention" className="bg-amber-500" />
          <Swatch name="urgent" className="bg-rose-500" />
        </div>
      </Section>

      <Section kicker="Foundation" title="Typography">
        <Card className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-ink-400">Display · Fraunces</p>
            <p className="font-display text-4xl font-semibold text-ink-900">Unlock learning.</p>
          </div>
          <div className="border-t border-ink-100 pt-4">
            <p className="text-xs uppercase tracking-widest text-ink-400">Body · Inter</p>
            <p className="max-w-2xl text-ink-600">
              Aanya practised long division four times this week and her average
              rose 12%. A clear, calm sentence a parent can act on — that’s the
              whole point.
            </p>
          </div>
        </Card>
      </Section>

      <Section kicker="Components" title="Buttons">
        <Card className="flex flex-wrap items-center gap-3">
          <Button>Generate summary</Button>
          <Button variant="ghost">Cancel</Button>
          <Button size="sm">Small</Button>
          <Button size="lg">Large</Button>
          <Button disabled>Disabled</Button>
        </Card>
      </Section>

      <Section kicker="Components" title="Badges">
        <Card className="flex flex-wrap gap-2">
          <Badge tone="brand">Unlocked</Badge>
          <Badge tone="neutral">Grade 8</Badge>
          <Badge tone="success">On track</Badge>
          <Badge tone="attention">Needs practice</Badge>
          <Badge tone="urgent">Sharp drop</Badge>
        </Card>
      </Section>

      <Section kicker="Components" title="Rich content (HTML + LaTeX)">
        <p className="mb-3 text-sm text-ink-500">
          Question text, MCQ options, hints, and worked solutions all flow
          through <code>&lt;RichContent /&gt;</code> — sanitised HTML with
          KaTeX-rendered math. One primitive, identical output everywhere.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <p className="mb-2 text-xs uppercase tracking-widest text-ink-400">Pure LaTeX</p>
            <RichContent
              variant="block"
              text={"The quadratic formula is $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$, and in block form: $$\\sqrt{3}\\over 2$$"}
            />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-widest text-ink-400">HTML + inline math</p>
            <RichContent
              variant="block"
              text={"<p>Find the value of <strong>x</strong> when \\(2x + 3 = 11\\).</p><p>Express your answer using <em>integers only</em>.</p>"}
            />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-widest text-ink-400">Worked solution with list</p>
            <RichContent
              variant="block"
              text={"<ol><li>Rearrange: \\(2x = 11 - 3\\).</li><li>Divide both sides by 2: \\(x = 4\\).</li></ol>"}
            />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-widest text-ink-400">Sanitiser drops scripts</p>
            <RichContent
              variant="block"
              text={"<script>alert(1)</script><p>Safe content: $E = mc^2$</p>"}
            />
          </Card>
        </div>
      </Section>

      <Section kicker="Components" title="Interactive widget (sandboxed)">
        <p className="mb-3 text-sm text-ink-500">
          Authored interactive questions (M7-11) run their embedded scripts in a
          <code>&lt;iframe sandbox=&quot;allow-scripts&quot;&gt;</code> with{' '}
          <strong>no</strong> <code>allow-same-origin</code> — so the script
          can&apos;t reach the app&apos;s cookies, storage, or DOM. Tokens are
          resolved server-side before delivery.
        </p>
        <Card>
          <InteractiveWidget
            minHeight={160}
            html={
              '<p>Drag the slider — the readout updates live (runs inside the sandbox):</p>' +
              '<input id="r" type="range" min="0" max="10" value="3" />' +
              '<p>Value: <b id="out">3</b></p>' +
              '<script>var r=document.getElementById("r"),o=document.getElementById("out");' +
              'r.addEventListener("input",function(){o.textContent=r.value;});</script>'
            }
          />
        </Card>
      </Section>

      <Section kicker="Components" title="Skeleton (loading)">
        <Card className="space-y-3">
          <Skeleton w="w-1/3" h="h-5" />
          <Skeleton w="w-full" h="h-4" />
          <Skeleton w="w-5/6" h="h-4" />
          <Skeleton w="w-2/3" h="h-4" />
        </Card>
      </Section>

      <Section kicker="Components" title="Surfaces & accents">
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <h3 className="font-display text-lg font-semibold text-ink-900">Warm card</h3>
            <p className="mt-1 text-sm text-ink-500">
              <code>.os-card</code> — white on warm paper, hairline border, soft
              elevation.
            </p>
          </Card>
          <Card>
            <h3 className="font-display text-lg font-semibold text-ink-900">
              Chalk underline
            </h3>
            <p className="mt-3 text-sm text-ink-500">
              The active-nav signature:{' '}
              <span className="chalk-underline font-semibold text-ink-800">Dashboard</span>
            </p>
          </Card>
        </div>
      </Section>
    </main>
  </div>
);
