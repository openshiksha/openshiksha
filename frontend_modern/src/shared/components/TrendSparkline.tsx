import type { ProficiencySnapshot } from '@/features/student/useProficiencyHistory';

interface Props {
  snapshots: ProficiencySnapshot[];
  width?: number;
  height?: number;
}

export const TrendSparkline = ({ snapshots, width = 80, height = 24 }: Props) => {
  if (snapshots.length < 2) return null;

  const scores = snapshots.map((s) => s.score);
  const min = Math.min(...scores);
  const max = Math.max(...scores);
  const range = max - min || 0.01;

  const points = scores
    .map((score, i) => {
      const x = (i / (scores.length - 1)) * width;
      const y = height - ((score - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  const trend = scores[scores.length - 1] - scores[0];
  const color = trend > 0.01 ? '#22c55e' : trend < -0.01 ? '#ef4444' : '#94a3b8';

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="inline-block"
      aria-hidden="true"
    >
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
