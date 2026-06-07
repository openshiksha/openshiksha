/**
 * Tests for the widget scaffolder (`npm run widget:new <kind>`).
 *
 * The pure helpers (`validateKind`, `kindToIdentifier`, `patchRegistry`)
 * are exercised directly. The end-to-end path (writing files + patching
 * the registry) is covered by running the script in a controlled
 * scratch directory so we never touch the real registry under
 * `src/widgets/`.
 */

import { describe, expect, it } from 'vitest';
import { kindToIdentifier, patchRegistry, validateKind } from './create-widget-utils.mjs';

describe('validateKind', () => {
  it('accepts hyphen-separated lowercase slugs', () => {
    expect(() => validateKind('number-line')).not.toThrow();
    expect(() => validateKind('function-plotter')).not.toThrow();
    expect(() => validateKind('fractionbar')).not.toThrow();
  });

  it('accepts framework-internal kinds with a leading underscore', () => {
    expect(() => validateKind('_hello')).not.toThrow();
    expect(() => validateKind('_dev-playground')).not.toThrow();
  });

  it('rejects empty / non-string input', () => {
    expect(() => validateKind('')).toThrow(/required|Invalid/);
    expect(() => validateKind(undefined)).toThrow();
    expect(() => validateKind(123)).toThrow();
  });

  it('rejects uppercase, spaces, leading digits, trailing hyphens', () => {
    expect(() => validateKind('NumberLine')).toThrow(/Invalid/);
    expect(() => validateKind('number line')).toThrow(/Invalid/);
    expect(() => validateKind('1st-widget')).toThrow(/Invalid/);
    expect(() => validateKind('trailing-')).toThrow(/Invalid/);
  });
});

describe('kindToIdentifier', () => {
  it('camelCases hyphen-separated slugs', () => {
    expect(kindToIdentifier('thermo-piston')).toBe('thermoPiston');
    expect(kindToIdentifier('number-line')).toBe('numberLine');
    expect(kindToIdentifier('function-plotter-2')).toBe('functionPlotter2');
  });

  it('leaves single-word slugs alone', () => {
    expect(kindToIdentifier('fractionbar')).toBe('fractionbar');
  });

  it('preserves the leading underscore on framework-internal kinds', () => {
    expect(kindToIdentifier('_hello')).toBe('_hello');
    expect(kindToIdentifier('_dev-playground')).toBe('_devPlayground');
  });
});

describe('patchRegistry', () => {
  const FIXTURE = `import _hello from './_hello';
import thermoPiston from './thermo-piston';
// widget:new import anchor — \`npm run widget:new <kind>\` appends new imports above this line.
import type { WidgetModule } from './_sdk/defineWidget';

export const widgetRegistry = {
  _hello,
  'thermo-piston': thermoPiston,
  // widget:new entry anchor — \`npm run widget:new <kind>\` appends new entries above this line.
} as const satisfies Record<string, WidgetModule>;
`;

  it('inserts the import line just before the import anchor', () => {
    const patched = patchRegistry(FIXTURE, 'number-line', 'numberLine');
    expect(patched).toContain("import numberLine from './number-line';\n// widget:new import anchor");
  });

  it('inserts the entry line just before the entry anchor', () => {
    const patched = patchRegistry(FIXTURE, 'number-line', 'numberLine');
    // The entry is added on its own line, before the existing entry anchor.
    expect(patched).toMatch(/'number-line': numberLine,\n {2}\/\/ widget:new entry anchor/);
  });

  it('leaves every previously-registered widget intact', () => {
    const patched = patchRegistry(FIXTURE, 'number-line', 'numberLine');
    expect(patched).toContain("import _hello from './_hello';");
    expect(patched).toContain("import thermoPiston from './thermo-piston';");
    expect(patched).toContain('_hello,');
    expect(patched).toContain("'thermo-piston': thermoPiston,");
  });

  it('throws if either anchor is missing', () => {
    const noImportAnchor = FIXTURE.replace('// widget:new import anchor', '// (removed)');
    expect(() => patchRegistry(noImportAnchor, 'x', 'x')).toThrow(/import anchor/);

    const noEntryAnchor = FIXTURE.replace('// widget:new entry anchor', '// (removed)');
    expect(() => patchRegistry(noEntryAnchor, 'x', 'x')).toThrow(/entry anchor/);
  });
});
