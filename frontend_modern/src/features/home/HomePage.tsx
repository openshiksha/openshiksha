import { Link } from 'react-router-dom';
import { Logo, Button } from '@/shared/ui';
import { useT, LanguageSwitcher, type LocaleKey } from '@/shared/i18n';

/**
 * V2 marketing home page. Echoes the legacy landing (chalkboard hero →
 * Practice/Evaluate/Analyse → mission + teacher photo → "Start now" → features)
 * in the "Chalk & Unlock" language, reusing the legacy hero images.
 * See docs/initiatives/2026-design-system-v2.md.
 */

const PILLARS: { titleKey: LocaleKey; descKey: LocaleKey; icon: React.ReactElement }[] = [
  {
    titleKey: 'home.pillarPracticeTitle',
    descKey: 'home.pillarPracticeDesc',
    icon: (
      <path d="M12 19l7-7a2.5 2.5 0 00-3.5-3.5l-7 7L5 19l3.5-.5z M14 6l4 4" strokeLinecap="round" strokeLinejoin="round" />
    ),
  },
  {
    titleKey: 'home.pillarEvaluateTitle',
    descKey: 'home.pillarEvaluateDesc',
    icon: <path d="M5 12.5l4 4 10-10" strokeLinecap="round" strokeLinejoin="round" />,
  },
  {
    titleKey: 'home.pillarAnalyseTitle',
    descKey: 'home.pillarAnalyseDesc',
    icon: (
      <path d="M5 19V5 M5 19h14 M8 16l3-4 3 2 4-6" strokeLinecap="round" strokeLinejoin="round" />
    ),
  },
];

const FEATURE_KEYS: LocaleKey[] = [
  'home.feature1',
  'home.feature2',
  'home.feature3',
  'home.feature4',
  'home.feature5',
  'home.feature6',
];

export const HomePage = () => {
  const t = useT();
  return (
    <div className="bg-paper text-ink-700">
      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <header className="absolute inset-x-0 top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Link to="/" aria-label="OpenShiksha home">
            <Logo size="md" wordmarkClassName="text-white" hideWordmarkOnMobile />
          </Link>
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <Link to="/login" className="text-sm font-semibold text-white/90 transition-colors hover:text-white">
              {t('home.loginArrow')}
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero — chalkboard heritage ──────────────────────────────────── */}
      <section className="relative isolate overflow-hidden">
        <img
          src="/home/blackboard-dark.jpg"
          alt=""
          aria-hidden="true"
          className="absolute inset-0 -z-10 h-full w-full object-cover"
        />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-ink-900/85 via-ink-900/75 to-ink-900/90" />

        <div className="mx-auto max-w-6xl px-6 pb-20 pt-32 sm:pt-40">
          <div className="max-w-3xl">
            <p className="animate-fade-up text-sm font-semibold uppercase tracking-[0.2em] text-brand-400">
              {t('auth.heroFootnote')}
            </p>
            <h1
              className="animate-fade-up mt-4 font-display text-5xl font-semibold leading-[1.05] text-white text-balance sm:text-6xl"
              style={{ animationDelay: '80ms' }}
            >
              {t('home.heroTitle')}
            </h1>
            <p
              className="animate-fade-up mt-5 max-w-xl text-lg leading-relaxed text-ink-100"
              style={{ animationDelay: '160ms' }}
            >
              {t('home.heroSubtitle')}
            </p>
            <div className="animate-fade-up mt-8 flex flex-wrap items-center gap-4" style={{ animationDelay: '240ms' }}>
              <Link to="/login">
                <Button size="lg">{t('home.login')}</Button>
              </Link>
              <Link to="/register/open">
                <Button variant="ghost" size="lg" className="!border-white/30 !text-white hover:!bg-white/10">
                  {t('home.startFree')}
                </Button>
              </Link>
            </div>
          </div>

          {/* Practice / Evaluate / Analyse */}
          <div className="animate-fade-up mt-16 grid gap-px overflow-hidden rounded-xl2 border border-white/10 bg-white/10 sm:grid-cols-3" style={{ animationDelay: '320ms' }}>
            {PILLARS.map((p) => (
              <div key={p.titleKey} className="bg-ink-900/40 p-6 backdrop-blur-sm">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-8 w-8 text-brand-500">
                  {p.icon}
                </svg>
                <h3 className="mt-4 font-display text-lg font-semibold text-white">{t(p.titleKey)}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-ink-200">{t(p.descKey)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Mission + teacher photo ─────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div className="overflow-hidden rounded-3xl border border-ink-100 shadow-card">
            <img src="/home/teacher.jpg" alt={t('home.teacherAlt')} className="h-full w-full object-cover" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-brand-700">
              {t('home.missionKicker')}
            </p>
            <h2 className="mt-3 font-display text-3xl font-semibold text-ink-900 text-balance">
              {t('home.missionTitle')}
            </h2>
            <div className="mt-5 space-y-4 text-ink-600 leading-relaxed">
              <p>{t('home.missionBody1')}</p>
              <p>
                {t('home.missionOpenPre')}{' '}
                <span className="font-semibold text-ink-800">{t('home.missionOpenTerm')}</span>{' '}
                {t('home.missionOpenPost')}{' '}
                <span className="font-semibold text-ink-800">{t('home.missionPartnerTerm')}</span>{' '}
                {t('home.missionPartnerPost')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Start now ───────────────────────────────────────────────────── */}
      <section className="bg-chalkboard">
        <div className="mx-auto max-w-6xl px-6 py-20 text-center">
          <Logo variant="mark" size="lg" float className="justify-center" />
          <h2 className="mt-6 font-display text-4xl font-semibold text-white">
            {t('home.startNowTitle')}
          </h2>
          <p className="mx-auto mt-3 max-w-md text-ink-200">{t('home.startNowSubtitle')}</p>
          <div className="mx-auto mt-8 grid max-w-2xl gap-4 sm:grid-cols-2">
            <Link
              to="/register/open"
              className="group rounded-xl2 border border-white/10 bg-white/5 p-6 text-left transition-colors hover:border-brand-500/60 hover:bg-white/10"
            >
              <h3 className="font-display text-xl font-semibold text-white">
                {t('home.studentsCardTitle')}
              </h3>
              <p className="mt-1 text-sm text-ink-200">{t('home.studentsCardDesc')}</p>
              <span className="mt-3 inline-block text-sm font-semibold text-brand-400 group-hover:text-brand-300">
                {t('home.studentsCardCta')}
              </span>
            </Link>
            <Link
              to="/enquire"
              className="group rounded-xl2 border border-white/10 bg-white/5 p-6 text-left transition-colors hover:border-brand-500/60 hover:bg-white/10"
            >
              <h3 className="font-display text-xl font-semibold text-white">
                {t('home.schoolsCardTitle')}
              </h3>
              <p className="mt-1 text-sm text-ink-200">{t('home.schoolsCardDesc')}</p>
              <span className="mt-3 inline-block text-sm font-semibold text-brand-400 group-hover:text-brand-300">
                {t('home.schoolsCardCta')}
              </span>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Key features ────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-display text-3xl font-semibold text-ink-900">
          {t('home.featuresTitle')}
        </h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURE_KEYS.map((key) => (
            <div key={key} className="os-card flex gap-3 p-5">
              <span aria-hidden className="mt-0.5 flex h-6 w-6 flex-none items-center justify-center rounded-full bg-brand-100">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} className="h-3.5 w-3.5 text-brand-700">
                  <path d="M5 12.5l4 4 10-10" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <p className="text-sm leading-relaxed text-ink-600">{t(key)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-ink-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <Logo size="sm" />
          <div className="flex items-center gap-6 text-sm text-ink-500">
            <Link to="/login" className="hover:text-ink-800">{t('home.login')}</Link>
            <Link to="/enquire" className="hover:text-ink-800">{t('home.footerSchools')}</Link>
            <a
              href="https://github.com/openshiksha/openshiksha"
              target="_blank"
              rel="noreferrer"
              className="hover:text-ink-800"
            >
              {t('home.footerGithub')}
            </a>
          </div>
          <p className="text-xs text-ink-400">© {new Date().getFullYear()} Social Seva Initiatives</p>
        </div>
      </footer>
    </div>
  );
};
