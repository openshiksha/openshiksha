/**
 * Tests for the IW-5 teacher widget gallery + schema-driven form.
 *
 * Coverage focuses on the parts where regressions would silently
 * mis-author content: the filtering rules (framework-internal + admin-
 * only kinds hidden), the schema → form mapping, default-config
 * derivation, and the Apply / Cancel callback contract. Drag-pointer
 * behaviour of any specific widget is covered by that widget's own
 * tests + the Playwright suite.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { WidgetGalleryPanel } from './WidgetGalleryPanel';

/** Lookup a config field by its predictable id (matches PropertyField). */
const field = (name: string) => document.getElementById(`wgf-${name}`) as HTMLInputElement;

describe('WidgetGalleryPanel', () => {
  it('lists teacher-visible widgets (thermo-piston, number-line) on the gallery grid', () => {
    render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
    // Each entry is rendered as a card-button whose accessible name includes
    // the widget title; query by role to disambiguate from description copy.
    expect(screen.getByRole('button', { name: /Thermodynamics/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Number line/i })).toBeInTheDocument();
  });

  it('hides framework-internal kinds (prefix `_`)', () => {
    render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
    // `_hello` exists in the registry but must never show in the gallery.
    expect(screen.queryByText(/_hello/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Hello widget/i)).not.toBeInTheDocument();
  });

  it('hides the admin-only custom-html kind from regular teachers', () => {
    render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
    // The kind label is `custom-html`. Make sure neither it nor the
    // (admin only) title slip into the visible gallery.
    expect(screen.queryByText(/custom-html/i)).not.toBeInTheDocument();
  });

  it('flags answer-producing widgets with an "answer" badge', () => {
    render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
    // number-line is answer-producing; the badge sits inside its card.
    expect(screen.getByText('answer')).toBeInTheDocument();
  });

  it('Cancel on the gallery grid fires onCancel', () => {
    const onCancel = vi.fn();
    render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={onCancel} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalled();
  });

  it('clicking a kind drops into the configure view with a back button', () => {
    render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /Number line/i }));
    expect(screen.getByText(/← back to gallery/i)).toBeInTheDocument();
    expect(screen.getByText('Config')).toBeInTheDocument();
    expect(screen.getByText('Preview')).toBeInTheDocument();
  });

  it('renders a labelled form field for every (non-deprecated) schema property', () => {
    render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /Number line/i }));
    // number-line schema declares min / max / step / initial / label —
    // every property gets an input keyed by the predictable `wgf-<name>` id.
    expect(field('min')).toBeInTheDocument();
    expect(field('max')).toBeInTheDocument();
    expect(field('step')).toBeInTheDocument();
    expect(field('initial')).toBeInTheDocument();
    expect(field('label')).toBeInTheDocument();
  });

  it('preselecting a kind via initialKind lands directly in configure mode', () => {
    render(
      <WidgetGalleryPanel
        initialKind="number-line"
        initialConfig={{ min: 5, max: 15 }}
        onApply={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText(/← back to gallery/i)).toBeInTheDocument();
    // The initial config values populate the form, not the schema defaults.
    expect(field('min').value).toBe('5');
    expect(field('max').value).toBe('15');
  });

  it('Use this widget surfaces { kind, config } to onApply', () => {
    const onApply = vi.fn();
    render(
      <WidgetGalleryPanel
        initialKind="number-line"
        onApply={onApply}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByText(/Use this widget/i));
    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({ kind: 'number-line', config: expect.any(Object) }),
    );
  });

  it('editing a field coerces numeric input to a Number before propagating', () => {
    const onApply = vi.fn();
    render(
      <WidgetGalleryPanel
        initialKind="number-line"
        onApply={onApply}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.change(field('min'), { target: { value: '42' } });
    fireEvent.click(screen.getByText(/Use this widget/i));
    const arg = onApply.mock.calls[0][0];
    expect(arg.config.min).toBe(42); // number, not "42"
  });
});
