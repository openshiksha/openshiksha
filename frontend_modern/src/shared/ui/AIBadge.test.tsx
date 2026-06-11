import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AIBadge } from './AIBadge';
import { isAIStub } from './aiProvenance';

describe('AIBadge', () => {
  it('labels genuine LLM output as AI-generated', () => {
    render(<AIBadge modelUsed="claude-sonnet-4-6" stubLabel="Auto-summary" />);
    expect(screen.getByText('✨ AI-generated')).toBeDefined();
    expect(screen.queryByText('Auto-summary')).toBeNull();
  });

  it('labels the deterministic stub with the surface-specific Auto label', () => {
    render(<AIBadge modelUsed="stub" stubLabel="Auto-strategy" />);
    expect(screen.getByText('Auto-strategy')).toBeDefined();
    expect(screen.queryByText('✨ AI-generated')).toBeNull();
  });

  it('falls back to a generic Auto label when none is given', () => {
    render(<AIBadge modelUsed="stub" />);
    expect(screen.getByText('Auto-generated')).toBeDefined();
  });
});

describe('isAIStub', () => {
  it('is true only for the stub sentinel', () => {
    expect(isAIStub('stub')).toBe(true);
    expect(isAIStub('claude-sonnet-4-6')).toBe(false);
    expect(isAIStub('')).toBe(false);
    expect(isAIStub(null)).toBe(false);
    expect(isAIStub(undefined)).toBe(false);
  });
});
