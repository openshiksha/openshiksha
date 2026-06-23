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

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { WidgetGalleryPanel } from './WidgetGalleryPanel';

/**
 * DTB-3 — stub the describe-to-build hook so the panel never reaches into
 * react-query (these tests render the panel without a QueryClientProvider).
 * Tests drive the proposal/fallback/error paths by configuring this object.
 */
const authoringMock = vi.hoisted(() => ({
  mutate: vi.fn(),
  isPending: false,
  isError: false,
}));

vi.mock('./useWidgetAuthoring', () => ({
  useWidgetAuthoring: () => authoringMock,
}));

beforeEach(() => {
  authoringMock.mutate = vi.fn();
  authoringMock.isPending = false;
  authoringMock.isError = false;
});

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

  // ── DTB-3: Describe-to-Build ───────────────────────────────────────
  describe('Describe-to-Build', () => {
    it('shows the describe prompt box on the gallery grid', () => {
      render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
      expect(screen.getByLabelText(/Describe it/i)).toBeInTheDocument();
      const generate = screen.getByRole('button', { name: /Generate widget/i });
      // Empty prompt → button disabled (nothing to send).
      expect(generate).toBeDisabled();
    });

    it('enables Generate once a description is typed and posts it', () => {
      render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
      fireEvent.change(screen.getByLabelText(/Describe it/i), {
        target: { value: 'a number line where students mark 3/4' },
      });
      const generate = screen.getByRole('button', { name: /Generate widget/i });
      expect(generate).not.toBeDisabled();
      fireEvent.click(generate);
      expect(authoringMock.mutate).toHaveBeenCalledWith(
        { description: 'a number line where students mark 3/4', allow_variables: false },
        expect.objectContaining({ onSuccess: expect.any(Function) }),
      );
    });

    it('real proposal → lands in configure view with AI-generated badge + the config', () => {
      // Drive the success callback with a genuine LLM proposal.
      authoringMock.mutate = vi.fn((_vars, opts) => {
        opts.onSuccess({
          widget_kind: 'number-line',
          widget_config: { min: 0, max: 1, step: 0.25, initial: 0.75, label: 'Mark 3/4' },
          model_used: 'claude-sonnet-4-6',
          ai_available: true,
          repaired: false,
          variable_constraints: {},
        });
      });
      render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
      fireEvent.change(screen.getByLabelText(/Describe it/i), {
        target: { value: 'a number line where students mark 3/4' },
      });
      fireEvent.click(screen.getByRole('button', { name: /Generate widget/i }));

      // We're now in the configure view, on the proposed kind.
      expect(screen.getByText(/← back to gallery/i)).toBeInTheDocument();
      // Honest provenance: real LLM → ✨ AI-generated, never the Auto badge.
      expect(screen.getByText(/AI-generated/i)).toBeInTheDocument();
      expect(screen.queryByText(/Auto-built/i)).not.toBeInTheDocument();
      // The proposed config populated the live preview's schema form.
      expect(field('initial').value).toBe('0.75');
      expect(field('label').value).toBe('Mark 3/4');
    });

    it('deterministic fallback → neutral Auto-built badge + friendly unavailable line', () => {
      // No key / timeout: backend returns the kind's safe default as a stub.
      authoringMock.mutate = vi.fn((_vars, opts) => {
        opts.onSuccess({
          widget_kind: 'number-line',
          widget_config: { min: 0, max: 10, step: 1, initial: 5, label: 'Number line' },
          model_used: 'stub',
          ai_available: false,
          repaired: false,
          variable_constraints: {},
        });
      });
      render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
      fireEvent.change(screen.getByLabelText(/Describe it/i), {
        target: { value: 'a number line' },
      });
      fireEvent.click(screen.getByRole('button', { name: /Generate widget/i }));

      // Stub is never shown as a real generation.
      expect(screen.getByText(/Auto-built/i)).toBeInTheDocument();
      expect(screen.queryByText(/✨ AI-generated/)).not.toBeInTheDocument();
      // Friendly "AI unavailable" line so the teacher knows what happened.
      expect(screen.getByText(/AI is unavailable right now/i)).toBeInTheDocument();
      // Still a working, editable starter config in the preview.
      expect(field('initial').value).toBe('5');
    });

    it('surfaces a friendly error when the builder call fails', () => {
      authoringMock.isError = true;
      render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
      expect(screen.getByRole('alert')).toHaveTextContent(/Couldn't reach the widget builder/i);
    });

    it('shows the generating label and disables the button while pending', () => {
      authoringMock.isPending = true;
      render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
      fireEvent.change(screen.getByLabelText(/Describe it/i), {
        target: { value: 'a number line' },
      });
      const generate = screen.getByRole('button', { name: /Building your widget/i });
      expect(generate).toBeDisabled();
    });

    // ── DTB-5b: per-student randomisation toggle ─────────────────────
    describe('per-student randomisation (DTB-5b)', () => {
      it('toggle is off by default → generate posts allow_variables: false', () => {
        render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
        expect(
          screen.getByLabelText(/Each student gets different numbers/i),
        ).not.toBeChecked();
        fireEvent.change(screen.getByLabelText(/Describe it/i), {
          target: { value: 'a number line' },
        });
        fireEvent.click(screen.getByRole('button', { name: /Generate widget/i }));
        expect(authoringMock.mutate).toHaveBeenCalledWith(
          { description: 'a number line', allow_variables: false },
          expect.anything(),
        );
      });

      it('checking the toggle sends allow_variables: true', () => {
        render(<WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />);
        fireEvent.click(screen.getByLabelText(/Each student gets different numbers/i));
        fireEvent.change(screen.getByLabelText(/Describe it/i), {
          target: { value: 'a number line where students mark a random fraction' },
        });
        fireEvent.click(screen.getByRole('button', { name: /Generate widget/i }));
        expect(authoringMock.mutate).toHaveBeenCalledWith(
          {
            description: 'a number line where students mark a random fraction',
            allow_variables: true,
          },
          expect.anything(),
        );
      });

      it('a randomised proposal shows the badge + bound tokens and forwards constraints on attach', () => {
        const constraints = { target: { min: 0, max: 1, integer: false, decimals: 2 } };
        authoringMock.mutate = vi.fn((_vars, opts) => {
          opts.onSuccess({
            widget_kind: 'number-line',
            widget_config: { min: 0, max: 1, step: 0.1, initial: '{{target}}', label: 'Mark it' },
            model_used: 'claude-sonnet-4-6',
            ai_available: true,
            repaired: false,
            variable_constraints: constraints,
          });
        });
        const onApply = vi.fn();
        render(<WidgetGalleryPanel onApply={onApply} onCancel={vi.fn()} />);
        fireEvent.click(screen.getByLabelText(/Each student gets different numbers/i));
        fireEvent.change(screen.getByLabelText(/Describe it/i), {
          target: { value: 'random fraction on a number line' },
        });
        fireEvent.click(screen.getByRole('button', { name: /Generate widget/i }));

        // On-screen wow: the randomised badge + the bound token name.
        expect(screen.getByText(/Randomized per student/i)).toBeInTheDocument();
        expect(screen.getByText(/\{\{target\}\}/)).toBeInTheDocument();

        // Attach forwards the validated constraints verbatim.
        fireEvent.click(screen.getByText(/Use this widget/i));
        expect(onApply).toHaveBeenCalledWith(
          expect.objectContaining({
            kind: 'number-line',
            variableConstraints: constraints,
          }),
        );
      });

      it('a non-randomised proposal shows no badge and attaches without constraints', () => {
        // Toggle on, but the AI chose concrete numbers → empty constraints.
        authoringMock.mutate = vi.fn((_vars, opts) => {
          opts.onSuccess({
            widget_kind: 'number-line',
            widget_config: { min: 0, max: 1, step: 0.25, initial: 0.75, label: 'Mark 3/4' },
            model_used: 'claude-sonnet-4-6',
            ai_available: true,
            repaired: false,
            variable_constraints: {},
          });
        });
        const onApply = vi.fn();
        render(<WidgetGalleryPanel onApply={onApply} onCancel={vi.fn()} />);
        fireEvent.click(screen.getByLabelText(/Each student gets different numbers/i));
        fireEvent.change(screen.getByLabelText(/Describe it/i), {
          target: { value: 'a number line where students mark 3/4' },
        });
        fireEvent.click(screen.getByRole('button', { name: /Generate widget/i }));

        expect(screen.queryByText(/Randomized per student/i)).not.toBeInTheDocument();
        fireEvent.click(screen.getByText(/Use this widget/i));
        expect(onApply).toHaveBeenCalledWith(
          expect.objectContaining({ kind: 'number-line', variableConstraints: undefined }),
        );
      });
    });
  });

  it('renders the gallery heading in Hindi when the locale is हिं', async () => {
    render(
      <I18nProvider initialLocale="hi">
        <WidgetGalleryPanel onApply={vi.fn()} onCancel={vi.fn()} />
      </I18nProvider>,
    );
    // इंटरैक्टिव विजेट = "interactive widget" per the Glossary register.
    await waitFor(() => {
      expect(screen.getByText(/इंटरैक्टिव विजेट/)).toBeInTheDocument();
    });
  });
});
