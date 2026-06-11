import { Badge } from './Badge';
import { isAIStub } from './aiProvenance';

interface AIBadgeProps {
  /** The serializer's `model_used` field — `'stub'` means no LLM ran. */
  modelUsed: string;
  /**
   * Label when the provider cascade fell back to the stub. Name what the
   * fallback *is* on this surface: "Auto-summary", "Auto-strategy",
   * "Auto-drafted", "Auto-explanation", …
   */
  stubLabel?: string;
  className?: string;
}

/**
 * Provider-transparency badge for every AI surface: brand-toned
 * `✨ AI-generated` for genuine LLM output, neutral `Auto-…` when the cascade
 * fell back to the deterministic stub. Deterministic output is still useful,
 * but must never be presented as AI. One vocabulary across student, teacher
 * and parent surfaces — pair with a short plain-language note on the stub
 * path explaining where the content came from.
 */
export const AIBadge = ({ modelUsed, stubLabel = 'Auto-generated', className }: AIBadgeProps) =>
  isAIStub(modelUsed) ? (
    <Badge tone="neutral" className={className}>
      {stubLabel}
    </Badge>
  ) : (
    <Badge tone="brand" className={className}>
      ✨ AI-generated
    </Badge>
  );
