import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { ResponsiveTable, type ResponsiveColumn } from './ResponsiveTable';

interface Row {
  id: number;
  chapter: string;
  avg: number;
}

const columns: ResponsiveColumn<Row>[] = [
  { key: 'chapter', header: 'Chapter', primary: true, cell: (r) => r.chapter },
  { key: 'avg', header: 'Avg', align: 'right', cell: (r) => `${r.avg}%` },
];

const rows: Row[] = [
  { id: 1, chapter: 'Polynomials', avg: 82 },
  { id: 2, chapter: 'Triangles', avg: 54 },
];

describe('<ResponsiveTable />', () => {
  it('renders a real table with headers and a row per item', () => {
    render(<ResponsiveTable rows={rows} columns={columns} rowKey={(r) => r.id} />);
    const table = screen.getByRole('table', { hidden: true });
    expect(within(table).getByText('Chapter')).toBeInTheDocument();
    expect(within(table).getByText('Avg')).toBeInTheDocument();
    // one header row + one row per item
    const bodyRows = within(table).getAllByRole('row', { hidden: true });
    expect(bodyRows).toHaveLength(rows.length + 1);
  });

  it('renders both the table (hidden on mobile) and the card list (hidden on desktop)', () => {
    const { container } = render(
      <ResponsiveTable rows={rows} columns={columns} rowKey={(r) => r.id} />,
    );
    // JSDOM cannot evaluate the media query, so assert both structures exist with
    // the correct breakpoint visibility classes.
    const table = container.querySelector('table');
    expect(table).not.toBeNull();
    expect(table?.className).toContain('hidden');
    expect(table?.className).toContain('sm:table');

    const list = container.querySelector('ul');
    expect(list).not.toBeNull();
    expect(list?.className).toContain('sm:hidden');
    expect(list?.querySelectorAll('li')).toHaveLength(rows.length);
  });

  it('renders the primary column as the card heading and the rest as label/value pairs', () => {
    const { container } = render(
      <ResponsiveTable rows={rows} columns={columns} rowKey={(r) => r.id} />,
    );
    const list = container.querySelector('ul')!;
    // primary value appears as a heading (outside the <dl>); secondary as <dt>/<dd>
    expect(within(list).getAllByText('Polynomials').length).toBeGreaterThan(0);
    expect(list.querySelectorAll('dt')).toHaveLength(rows.length); // one "Avg" label per card
    expect(within(list).getByText('82%')).toBeInTheDocument();
  });

  it('uses rowKey for keys without throwing on duplicate-looking content', () => {
    const dupRows: Row[] = [
      { id: 10, chapter: 'Same', avg: 50 },
      { id: 11, chapter: 'Same', avg: 50 },
    ];
    const { container } = render(
      <ResponsiveTable rows={dupRows} columns={columns} rowKey={(r) => r.id} />,
    );
    expect(container.querySelectorAll('ul > li')).toHaveLength(2);
  });

  it('renders only the caption/headers when rows is empty', () => {
    const { container } = render(
      <ResponsiveTable rows={[]} columns={columns} rowKey={(r) => r.id} caption="Empty demo" />,
    );
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0);
    expect(container.querySelectorAll('ul > li')).toHaveLength(0);
    expect(screen.getByText('Empty demo')).toBeInTheDocument();
  });
});
