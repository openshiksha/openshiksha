import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Input, Textarea, Select } from './Input';

describe('<Input />', () => {
  it('renders with a label associated to the input', () => {
    render(<Input label="Email" placeholder="you@example.com" />);
    const input = screen.getByLabelText('Email');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', 'you@example.com');
  });

  it('shows hint text when provided and no error', () => {
    render(<Input label="Name" hint="As shown on your school ID" />);
    expect(screen.getByText('As shown on your school ID')).toBeInTheDocument();
  });

  it('shows error and sets aria-invalid when error is set', () => {
    render(<Input label="Name" error="Required" />);
    const input = screen.getByLabelText('Name');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByText('Required')).toBeInTheDocument();
  });

  it('renders disabled state', () => {
    render(<Input label="Name" disabled />);
    expect(screen.getByLabelText('Name')).toBeDisabled();
  });
});

describe('<Textarea />', () => {
  it('renders a labelled multiline field', () => {
    render(<Textarea label="Bio" placeholder="Tell us…" />);
    const field = screen.getByLabelText('Bio');
    expect(field.tagName).toBe('TEXTAREA');
  });
});

describe('<Select />', () => {
  it('renders a labelled select with options', () => {
    render(
      <Select label="Board" defaultValue="CBSE">
        <option value="CBSE">CBSE</option>
        <option value="ICSE">ICSE</option>
      </Select>,
    );
    const field = screen.getByLabelText('Board') as HTMLSelectElement;
    expect(field.tagName).toBe('SELECT');
    expect(field.value).toBe('CBSE');
  });
});
