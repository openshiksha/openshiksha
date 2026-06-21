import { useT } from '@/shared/i18n';
import type { LocaleKey } from '@/shared/i18n';
import type { MilestoneTier } from './useStreak';

interface TierConfig {
  icon: string;
  labelKey: LocaleKey;
  bgColor: string;
  borderColor: string;
  textColor: string;
}

// Milestone tiers escalate through brand-warm tones to amber, capped by brand.
const TIER_CONFIG: Record<Exclude<MilestoneTier, 'none'>, TierConfig> = {
  starter: {
    icon: '🔥',
    labelKey: 'streak.tierStarter',
    bgColor: 'bg-brand-50',
    borderColor: 'border-brand-200',
    textColor: 'text-brand-700',
  },
  week: {
    icon: '⚡',
    labelKey: 'streak.tierWeek',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    textColor: 'text-amber-800',
  },
  month: {
    icon: '🌟',
    labelKey: 'streak.tierMonth',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-300',
    textColor: 'text-amber-900',
  },
  champion: {
    icon: '👑',
    labelKey: 'streak.tierChampion',
    bgColor: 'bg-brand-100',
    borderColor: 'border-brand-300',
    textColor: 'text-brand-800',
  },
};

interface StreakBadgeProps {
  streak: number;
  tier: MilestoneTier;
  longestStreak: number;
  graceUsed: boolean;
}

export const StreakBadge = ({ streak, tier, longestStreak, graceUsed }: StreakBadgeProps) => {
  const t = useT();

  if (streak === 0 || tier === 'none') {
    return (
      <div className="inline-flex items-center gap-1.5 bg-ink-50 border border-ink-200 text-ink-500 text-xs font-semibold px-3 py-1 rounded-full mt-2">
        <span>🔥</span>
        <span>{t('streak.days', { count: streak })}</span>
      </div>
    );
  }

  const config = TIER_CONFIG[tier];

  return (
    <div
      className={`inline-flex items-center gap-1.5 ${config.bgColor} border ${config.borderColor} ${config.textColor} text-xs font-semibold px-3 py-1 rounded-full mt-2`}
    >
      <span>{config.icon}</span>
      <span>{t('streak.days', { count: streak })}</span>
      {/* Secondary labels are de-emphasised by weight (`font-normal` vs the
          badge's `font-semibold`), NOT opacity: an `opacity-70/60` overlay
          dropped the tinted text below the 4.5:1 AA contrast bar against the
          badge fill (A11Y-7). The tier `textColor` tokens clear AA on their own
          fill at full opacity. */}
      <span className="font-normal">· {t(config.labelKey)}</span>
      {longestStreak > streak && (
        <span className="font-normal">· {t('streak.best', { count: longestStreak })}</span>
      )}
      {graceUsed && (
        <span className="font-normal" title={t('streak.graceTitle')}>
          · {t('streak.grace')}
        </span>
      )}
    </div>
  );
};
