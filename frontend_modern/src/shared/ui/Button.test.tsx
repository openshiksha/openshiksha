import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('<Button />', () => {
  it('renders children as a button with type="button" by default', () => {
    render(<Button>Save</Button>);
    const btn = screen.getByRole('button', { name: 'Save' });
    expect(btn.tagName).toBe('BUTTON');
    expect(btn).toHaveAttribute('type', 'button');
  });

  it('applies brand and ghost variant classes', () => {
    const { rerender } = render(<Button variant="brand">Brand</Button>);
    expect(screen.getByRole('button', { name: 'Brand' })).toHaveClass('btn-brand');

    rerender(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole('button', { name: 'Ghost' })).toHaveClass('btn-ghost');
  });

  it('applies size utilities for sm/lg and none for md', () => {
    const { rerender } = render(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button', { name: 'Large' })).toHaveClass('px-6', 'py-3', 'text-base');

    rerender(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button', { name: 'Small' })).toHaveClass('px-3.5', 'py-1.5', 'text-sm');

    rerender(<Button size="md">Medium</Button>);
    const md = screen.getByRole('button', { name: 'Medium' });
    expect(md).not.toHaveClass('px-6');
    expect(md).not.toHaveClass('px-3.5');
  });

  it('merges a passed className instead of replacing base classes', () => {
    render(
      <Button variant="brand" className="extra-class">
        Merge
      </Button>,
    );
    const btn = screen.getByRole('button', { name: 'Merge' });
    expect(btn).toHaveClass('btn-brand');
    expect(btn).toHaveClass('extra-class');
  });

  it('fires onClick and forwards props', () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} disabled aria-label="go">
        Go
      </Button>,
    );
    const btn = screen.getByRole('button', { name: 'go' });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    // disabled buttons do not fire click in the browser; re-test enabled
  });

  it('fires onClick when enabled', () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} data-testid="cta">
        Go
      </Button>,
    );
    fireEvent.click(screen.getByTestId('cta'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
