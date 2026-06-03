import type { MilestoneTier } from './useStreak';

interface TierConfig {
  icon: string;
  label: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
}

const TIER_CONFIG: Record<Exclude<MilestoneTier, 'none'>, TierConfig> = {
  starter: {
    icon: '🔥',
    label: 'On Fire',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-700',
  },
  week: {
    icon: '⚡',
    label: 'Week Warrior',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-700',
  },
  month: {
    icon: '🌟',
    label: 'Month Master',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    textColor: 'text-amber-700',
  },
  champion: {
    icon: '👑',
    label: 'Champion',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-700',
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
      <div className="inline-flex items-center gap-1.5 bg-gray-50 border border-gray-200 text-gray-500 text-xs font-semibold px-3 py-1 rounded-full mt-2">
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
