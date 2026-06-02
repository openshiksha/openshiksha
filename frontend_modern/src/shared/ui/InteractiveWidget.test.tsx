import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { InteractiveWidget } from './InteractiveWidget';

// M7-11: the widget must run authored scripts in a sandboxed iframe that CANNOT
// reach the app origin (no allow-same-origin), and must never inject the raw
// widget HTML into the app DOM.

describe('InteractiveWidget', () => {
  it('renders a sandboxed iframe with allow-scripts but NOT allow-same-origin', () => {
    const { container } = render(
      <InteractiveWidget html="<p>sim</p><script>var x=1;</script>" />
    );
    const iframe = container.querySelector('iframe');
    expect(iframe).not.toBeNull();
    const sandbox = iframe!.getAttribute('sandbox') ?? '';
    expect(sandbox).toContain('allow-scripts');
    expect(sandbox).not.toContain('allow-same-origin');
  });

  it('puts the resolved widget HTML (with image URL + substituted values) in srcDoc', () => {
    const html =
      '<img src="https://raw.githubusercontent.com/openshiksha/openshiksha-cabinet/HEAD/q/8.gif">' +
      '<script>var base = 3;</script>';
    const { container } = render(<InteractiveWidget html={html} />);
    const srcDoc = container.querySelector('iframe')!.getAttribute('srcdoc') ?? '';
    expect(srcDoc).toContain('raw.githubusercontent.com/openshiksha/openshiksha-cabinet/HEAD/q/8.gif');
    expect(srcDoc).toContain('var base = 3;');
    // jQuery + jQuery-UI are loaded for the legacy widgets.
    expect(srcDoc).toContain('jquery');
    expect(srcDoc).toContain('jquery-ui');
  });

  it('does NOT inject the raw widget HTML into the app DOM', () => {
    const { container } = render(
      <InteractiveWidget html="<script>window.__pwned = true;</script>" />
    );
    // The script lives only inside the iframe srcdoc, never as a real DOM node.
    expect(container.querySelector('script')).toBeNull();
  });

  it('renders the sanitised fallback (no iframe) when there is no widget HTML', () => {
    const { container } = render(
      <InteractiveWidget html="" fallbackText="<p>Static prompt</p>" />
    );
    expect(container.querySelector('iframe')).toBeNull();
    expect(container.textContent).toContain('Static prompt');
  });
});
