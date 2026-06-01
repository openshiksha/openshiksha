import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { RichContent } from './RichContent';
import { renderRichContent } from './renderRichContent';

describe('renderRichContent', () => {
  it('returns empty string for empty input', () => {
    expect(renderRichContent('')).toBe('');
  });

  it('renders inline LaTeX in $…$ delimiters via KaTeX', () => {
    const html = renderRichContent('Solve $x^2 + 1 = 0$.');
    expect(html).toContain('class="katex"');
    expect(html).not.toContain('$x^2');
  });

  it('renders block LaTeX in $$…$$ delimiters as displayMode', () => {
    const html = renderRichContent('Identity: $$a^2 + b^2 = c^2$$');
    expect(html).toContain('katex-display');
  });

  it('recognises \\(…\\) as inline (not displayMode)', () => {
    const html = renderRichContent('Inline \\(x^2\\) here.');
    expect(html).toContain('class="katex"');
    expect(html).not.toContain('katex-display');
  });

  it('recognises \\[…\\] as block math', () => {
    const html = renderRichContent('Block: \\[x^2\\]');
    expect(html).toContain('katex-display');
  });

  it('strips <script> tags', () => {
    const html = renderRichContent('<script>alert(1)</script><p>safe</p>');
    expect(html).not.toContain('alert(1)');
    expect(html).not.toContain('<script');
    expect(html).toContain('<p>safe</p>');
  });

  it('strips javascript: URLs from images', () => {
    const html = renderRichContent('<img src="javascript:alert(1)" alt="x" />');
    expect(html).not.toContain('javascript:');
  });

  it('keeps allowlisted tags (strong, em, sup, sub, img, ul/li, table)', () => {
    const html = renderRichContent(
      '<p><strong>A</strong> <em>b</em> H<sub>2</sub>O x<sup>2</sup></p>' +
        '<ul><li>one</li></ul>' +
        '<img src="https://example.com/x.png" alt="x" />' +
        '<table><tr><td>cell</td></tr></table>'
    );
    expect(html).toContain('<strong>');
    expect(html).toContain('<em>');
    expect(html).toContain('<sub>');
    expect(html).toContain('<sup>');
    expect(html).toContain('<ul>');
    expect(html).toContain('<li>one</li>');
    expect(html).toContain('<img');
    expect(html).toContain('https://example.com/x.png');
    expect(html).toContain('<table>');
    expect(html).toContain('<td>cell</td>');
  });

  it('renders LaTeX nested inside an HTML wrapper', () => {
    const html = renderRichContent('<p>The value of \\(x\\) is 2.</p>');
    expect(html).toContain('<p>');
    expect(html).toContain('class="katex"');
  });

  it('renders an un-delimited \\begin{array}…\\end{array} environment as block math', () => {
    const fixture =
      'Consider the table \\begin{array}{c|lcr} a & b & c & d \\\\ \\hline 1 & 2 & 3 & 4 \\end{array} above.';
    const html = renderRichContent(fixture);
    expect(html).toContain('katex-display');
    expect(html).not.toContain('\\begin{array}');
    expect(html).not.toContain('\\end{array}');
  });

  it('treats the env as a single math chunk even when it contains inner $-like chars', () => {
    // The `&` separators and `\\` row breaks must not be partially eaten by the
    // `$…$` delimiter regex — the env wraps the whole region.
    const fixture = 'X \\begin{array}{cc} \\$1 & 2 \\\\ 3 & 4 \\end{array} Y';
    const html = renderRichContent(fixture);
    expect(html).toContain('katex-display');
    // No raw begin/end tokens leak as text.
    expect(html).not.toMatch(/\\begin\{array\}/);
    expect(html).not.toMatch(/\\end\{array\}/);
  });

  it('does not crash on a truncated \\begin{ with no matching \\end', () => {
    expect(() =>
      renderRichContent('Truncated: \\begin{array}{c} 1 & 2 with no closer.')
    ).not.toThrow();
    const html = renderRichContent('Truncated: \\begin{array}{c} 1 & 2 with no closer.');
    // The bare tokens stay as escaped text (no katex render); important is no crash.
    expect(html).toContain('Truncated');
  });

  it('renders nested HTML wrapping inline LaTeX (the Cabinet `<div>…\\(…\\)…</div>` case)', () => {
    const html = renderRichContent('<div>Value is \\(2x+3\\) here.</div>');
    expect(html).toContain('<div>');
    expect(html).toContain('class="katex"');
    expect(html).not.toContain('\\(2x+3\\)');
  });

  it('renders an HTML <table> alongside inline KaTeX without leaking either', () => {
    const fixture =
      '<table><tr><td>Salary</td><td>$\\frac{a}{b}$</td></tr></table>';
    const html = renderRichContent(fixture);
    expect(html).toContain('<table>');
    expect(html).toContain('<td>Salary</td>');
    expect(html).toContain('class="katex"');
    expect(html).not.toContain('$\\frac');
  });

  it('renders a Cabinet-style fragment with HTML + inline LaTeX', () => {
    const fixture =
      '<p>Find <strong>x</strong> such that \\(2x + 3 = 11\\).</p>' +
      '<p>Express in $\\frac{a}{b}$ form.</p>';
    const html = renderRichContent(fixture);
    expect(html).toContain('<strong>x</strong>');
    // Two KaTeX-rendered spans expected.
    const matches = html.match(/class="katex"/g) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(2);
  });
});

describe('<RichContent />', () => {
  it('renders nothing for empty text', () => {
    const { container } = render(<RichContent text="" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders sanitised HTML + math into the DOM', () => {
    const { container } = render(
      <RichContent text="<p>Solve $x^2 = 4$.</p>" variant="block" />
    );
    expect(container.querySelector('.prose-osh')).not.toBeNull();
    expect(container.querySelector('.katex')).not.toBeNull();
    expect(container.querySelector('script')).toBeNull();
  });
});
