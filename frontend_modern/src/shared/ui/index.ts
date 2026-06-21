// OpenShiksha V2 design-system primitives.
// Import from here: `import { Button, Card, Badge, Logo } from '@/shared/ui'`.
// Every new primitive must be exported here AND rendered in features/design.
//
// `RichContent` / `renderRichContent` / `InteractiveWidget` are intentionally
// NOT re-exported from this barrel. They depend on DOMPurify (~25 kB) — and
// `InteractiveWidget` transitively re-pulls `RichContent` as its fallback
// renderer. Only question-rendering surfaces need them. Pulling them through
// the barrel forces eager pages like `LoginPage` (which only needs
// `{ Logo, Button }`) to drag DOMPurify into the first-paint critical path.
// Import them directly from `@/shared/ui/RichContent` /
// `@/shared/ui/InteractiveWidget` instead.
export { Logo } from './Logo';
export { Button } from './Button';
export { Card } from './Card';
export { Badge } from './Badge';
export { AIBadge } from './AIBadge';
export { isAIStub } from './aiProvenance';
export { Skeleton } from './Skeleton';
export { LoadingSpinner } from './LoadingSpinner';
export { ErrorBoundary } from './ErrorBoundary';
export { Input, Textarea, Select } from './Input';
export { Stat } from './Stat';
export { SectionHeading } from './SectionHeading';
export { EmptyState } from './EmptyState';
export { ResponsiveTable } from './ResponsiveTable';
export type { ResponsiveColumn } from './ResponsiveTable';
