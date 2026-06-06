import {
  Logo,
  Button,
  Card,
  Badge,
  RichContent,
  InteractiveWidget,
  Skeleton,
  LoadingSpinner,
  Input,
  Textarea,
  Select,
  Stat,
  SectionHeading,
  EmptyState,
} from '@/shared/ui';

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

      <Section kicker="Interactive Widgets · IW-1c" title="Runtime preview (framework path)">
        <p className="mb-3 text-sm text-ink-500">
          The new <strong>Widgets Framework</strong> path renders a registered
          widget kind through the SDK runtime — no raw HTML, no jQuery.
          Contributors write one file at{' '}
          <code>src/widgets/&lt;kind&gt;/index.ts</code> calling{' '}
          <code>defineWidget()</code>; the host serialises the render function,
          inlines it in the sandbox srcdoc, and wraps it with{' '}
          <code>reportValue</code> / <code>requestResize</code> hooks. The
          <code>_hello</code> widget below is the IW-1 end-to-end proof.
        </p>
        <Card>
          <InteractiveWidget
            minHeight={120}
            kind="_hello"
            config={{ kind: '_hello' }}
          />
        </Card>
        <p className="mt-3 text-xs text-ink-400">
          Try{' '}
          <code>
            &lt;InteractiveWidget kind=&quot;not-real&quot; config=&#123;&#123;&#125;&#125; /&gt;
          </code>{' '}
          to see the typed-error fallback.
        </p>
      </Section>

      <Section kicker="Interactive Widgets · IW-2" title="thermo-piston (legacy Class-11 sim, re-skinned)">
        <p className="mb-3 text-sm text-ink-500">
          The first non-stub widget on the framework: a re-implementation of
          Cabinet question <code>1/1/11/3/44/22</code> (Class-11 Thermodynamics,
          First Law). Same physics (ΔU = ΔQ − ΔW) and the same slider /
          piston / readout story as the legacy — but no jQuery, no embedded
          <code>&lt;script&gt;</code>, no Bootstrap glyphicons. ~280 KB of
          vendor head dropped; ~3 KB of vanilla SVG took its place. Per-student
          variables flow through <code>ctx.variables</code> the same way the
          croupier substitutes them server-side.
        </p>
        <Card>
          <InteractiveWidget
            minHeight={160}
            kind="thermo-piston"
            config={{}}
            variables={{ k: 80, j: 30 }}
          />
        </Card>
      </Section>

      <Section kicker="Components" title="Form inputs">
        <Card className="grid gap-4 sm:grid-cols-2">
          <Input label="Full name" placeholder="Aanya Sharma" />
          <Input
            label="School email"
            type="email"
            placeholder="you@school.edu"
            hint="We only use this to send progress digests."
          />
          <Input label="Roll number" defaultValue="07-A" disabled />
          <Input label="Phone" placeholder="+91" error="Enter a valid 10-digit number." />
          <Select label="Board" defaultValue="CBSE">
            <option value="CBSE">CBSE</option>
            <option value="ICSE">ICSE</option>
            <option value="STATE">State board</option>
          </Select>
          <Textarea label="Notes" placeholder="Anything we should know?" rows={3} />
        </Card>
      </Section>

      <Section kicker="Components" title="Stats (KPI block)">
        <Card className="grid gap-6 sm:grid-cols-3">
          <Stat label="Current streak" value="14d" delta="+2 days" tone="success" hint="Personal best" />
          <Stat label="Mastery" value="84%" delta="+6%" tone="brand" />
          <Stat label="Due" value="3" hint="of 5 assignments" />
        </Card>
      </Section>

      <Section kicker="Components" title="Section heading">
        <Card className="space-y-6">
          <SectionHeading eyebrow="Today" title="Practice queue" description="Pick something to work on right now." action={<a href="#" className="text-sm font-semibold text-brand-700 hover:text-brand-800">View all</a>} />
          <div className="border-t border-ink-100" />
          <SectionHeading title="Recent activity" />
        </Card>
      </Section>

      <Section kicker="Components" title="Empty state">
        <div className="grid gap-4 sm:grid-cols-2">
          <EmptyState
            title="No assignments yet"
            description="Your teacher hasn't assigned anything yet — but you can keep practicing."
            action={<Button>Browse practice</Button>}
          />
          <EmptyState title="No streak yet" description="Answer one question today to start the chain." />
        </div>
      </Section>

      <Section kicker="Components" title="Skeleton (loading)">
        <Card className="space-y-3">
          <Skeleton w="w-1/3" h="h-5" />
          <Skeleton w="w-full" h="h-4" />
          <Skeleton w="w-5/6" h="h-4" />
          <Skeleton w="w-2/3" h="h-4" />
        </Card>
      </Section>

      <Section kicker="States" title="Loading spinner">
        <Card className="flex flex-wrap items-center gap-8">
          <div className="flex flex-col items-center gap-2">
            <LoadingSpinner size="sm" />
            <span className="text-xs text-ink-500">sm</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <LoadingSpinner size="md" />
            <span className="text-xs text-ink-500">md</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <LoadingSpinner size="lg" />
            <span className="text-xs text-ink-500">lg</span>
          </div>
          <p className="ml-auto max-w-xs text-xs text-ink-500">
            Honours <code>prefers-reduced-motion</code> — the ring is static when
            reduced motion is requested.
          </p>
        </Card>
      </Section>

      <Section kicker="States" title="404 / error boundary">
        <Card>
          <p className="mb-3 text-sm text-ink-500">
            Unknown URLs render <code>NotFoundPage</code> (the catch-all route).
            Render-time errors anywhere under the router render the
            <code> ErrorBoundary</code> fallback. Both surfaces use the warm
            paper background, brand keyhole motif, and a single primary action.
          </p>
          <div className="flex flex-wrap gap-3">
            <a href="/this-route-does-not-exist" className="btn-ghost">Preview 404</a>
          </div>
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
