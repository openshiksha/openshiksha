import type { MilestoneTier } from './useStreak';

interface TierConfig {
  icon: string;
  label: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
}

// Milestone tiers escalate through brand-warm tones to amber, capped by brand.
const TIER_CONFIG: Record<Exclude<MilestoneTier, 'none'>, TierConfig> = {
  starter: {
    icon: '🔥',
    label: 'On Fire',
    bgColor: 'bg-brand-50',
    borderColor: 'border-brand-200',
    textColor: 'text-brand-700',
  },
  week: {
    icon: '⚡',
    label: 'Week Warrior',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    textColor: 'text-amber-800',
  },
  month: {
    icon: '🌟',
    label: 'Month Master',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-300',
    textColor: 'text-amber-900',
  },
  champion: {
    icon: '👑',
    label: 'Champion',
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
  if (streak === 0 || tier === 'none') {
    return (
      <div className="inline-flex items-center gap-1.5 bg-ink-50 border border-ink-200 text-ink-500 text-xs font-semibold px-3 py-1 rounded-full mt-2">
        <span>🔥</span>
        <span>{streak}-day streak</span>
      </div>
    );
  }

  const config = TIER_CONFIG[tier];

  return (
    <div
      className={`inline-flex items-center gap-1.5 ${config.bgColor} border ${config.borderColor} ${config.textColor} text-xs font-semibold px-3 py-1 rounded-full mt-2`}
    >
      <span>{config.icon}</span>
      <span>{streak}-day streak</span>
      <span className="font-normal opacity-70">· {config.label}</span>
      {longestStreak > streak && (
        <span className="font-normal opacity-60">· best: {longestStreak}</span>
      )}
      {graceUsed && (
        <span
          className="font-normal opacity-60"
          title="Grace day used — streak preserved through one missed day"
        >
          · grace ✓
        </span>
      )}
    </div>
  );
};
