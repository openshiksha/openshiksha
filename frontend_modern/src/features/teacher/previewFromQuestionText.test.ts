import { describe, expect, it } from 'vitest';
import { previewFromQuestionText } from './previewFromQuestionText';

describe('previewFromQuestionText', () => {
  it('returns "(no text)" for null/undefined/empty', () => {
    expect(previewFromQuestionText(null)).toBe('(no text)');
    expect(previewFromQuestionText(undefined)).toBe('(no text)');
    expect(previewFromQuestionText('')).toBe('(no text)');
    expect(previewFromQuestionText('   ')).toBe('(no text)');
  });

  it('strips simple HTML tags', () => {
    expect(previewFromQuestionText('<div>Hello world</div>')).toBe('Hello world');
    expect(previewFromQuestionText('<p>A <strong>bold</strong> claim</p>')).toBe(
      'A bold claim',
    );
  });

  it('cleans the broken-picker example: <div>Graph 1</div>', () => {
    // Exactly the row from the screenshot.
    expect(previewFromQuestionText('<div>Graph 1</div>')).toBe('Graph 1');
  });

  it('handles \\(…\\) inline LaTeX from cabinet questions', () => {
    // Another row from the screenshot.
    const raw =
      '<div>If \\(\\alpha \\) and \\(\\beta \\) are the zeros of the given polynomial \\(f(x)=ax^2+bx+c\\)';
    const out = previewFromQuestionText(raw);
    expect(out).not.toContain('\\(');
    expect(out).not.toContain('<div');
    expect(out).toContain('[math]');
    expect(out).toContain('are the zeros of the given polynomial');
  });

  it('replaces {{var}} tokens with "?" (per-student values not picked yet)', () => {
    const raw =
      '<div>Sum of the zeros of a quadratic equation {{j+k}} and product of the zeros is';
    const out = previewFromQuestionText(raw);
    expect(out).not.toContain('{{');
    expect(out).toContain('?');
    expect(out).toContain('Sum of the zeros of a quadratic equation');
  });

  it('collapses block math $$…$$, \\[…\\], and inline $…$', () => {
    expect(previewFromQuestionText('Solve $x^2 + 1 = 0$.')).toBe('Solve [math] .');
    expect(previewFromQuestionText('Block: $$E = mc^2$$ end')).toBe('Block: [math] end');
    expect(previewFromQuestionText('Bracket: \\[a + b\\] end')).toBe('Bracket: [math] end');
  });

  it('collapses un-delimited LaTeX environments (\\begin{array}…\\end{array})', () => {
    const raw = 'Table: \\begin{array}{c|lcr} Salary & \\text{1000-3000} \\end{array} done';
    expect(previewFromQuestionText(raw)).toBe('Table: [math] done');
  });

  it('decodes common HTML entities', () => {
    expect(previewFromQuestionText('Tea&nbsp;&amp;&nbsp;biscuits')).toBe('Tea & biscuits');
    expect(previewFromQuestionText('&lt;tag&gt;')).toBe('<tag>');
    expect(previewFromQuestionText('She said &quot;hi&quot;')).toBe('She said "hi"');
  });

  it('truncates long previews to 120 chars with an ellipsis', () => {
    const long = 'A '.repeat(200); // 400 chars
    const out = previewFromQuestionText(long);
    expect(out.length).toBeLessThanOrEqual(121);
    expect(out.endsWith('…')).toBe(true);
  });

  it('preserves short clean text unchanged', () => {
    expect(previewFromQuestionText('Find the sum of two integers.')).toBe(
      'Find the sum of two integers.',
    );
  });

  it('handles real cabinet-style nested markup end to end', () => {
    // First row from the user's screenshot — compound prompt.
    const raw =
      '<div>From the expressions given below, select the one(s) which cannot be termed</div>';
    expect(previewFromQuestionText(raw)).toBe(
      'From the expressions given below, select the one(s) which cannot be termed',
    );
  });
});
