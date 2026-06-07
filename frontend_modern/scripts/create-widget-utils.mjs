/** kind slug -> camelCase identifier for the registry import binding. */
export function kindToIdentifier(kind) {
  // Leave leading underscore alone (framework-internal widgets like `_hello`).
  const leading = kind.startsWith('_') ? '_' : '';
  const body = (leading ? kind.slice(1) : kind)
    .split('-')
    .map((seg, i) => (i === 0 ? seg : seg.charAt(0).toUpperCase() + seg.slice(1)))
    .join('');
  return leading + body;
}

/** Reject kinds that won't fit the framework's contract. */
export function validateKind(kind) {
  if (typeof kind !== 'string' || kind.length === 0) {
    throw new Error('kind is required');
  }
  if (!/^_?[a-z][a-z0-9]*(-[a-z0-9]+)*$/.test(kind)) {
    throw new Error(
      `Invalid kind "${kind}". Must be lowercase, hyphen-separated, ` +
        'start with a letter (or underscore for framework-internal kinds), e.g. "number-line".',
    );
  }
}

/**
 * Apply the two anchor edits to `registry.ts`. Pure string transforms so
 * the unit test can run them without touching disk.
 */
export function patchRegistry(source, kind, ident) {
  const importAnchor = '// widget:new import anchor';
  const entryAnchor = '// widget:new entry anchor';
  if (!source.includes(importAnchor)) {
    throw new Error(`registry.ts is missing the import anchor comment ("${importAnchor}")`);
  }
  if (!source.includes(entryAnchor)) {
    throw new Error(`registry.ts is missing the entry anchor comment ("${entryAnchor}")`);
  }
  // Imports live at column 0; just push a new import line above the anchor.
  const importLine = `import ${ident} from './${kind}';\n`;
  const withImport = source.replace(importAnchor, importLine + importAnchor);
  // The entry anchor is preceded by its own 2-space indent in the source.
  // Replace just the anchor (not its indent) so the existing indentation lands
  // in front of our new entry and the anchor keeps the same 2-space indent.
  const entryContent = `'${kind}': ${ident},`;
  return withImport.replace(entryAnchor, entryContent + '\n  ' + entryAnchor);
}
