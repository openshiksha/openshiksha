// jest-dom matcher types for Vitest 5.
//
// @testing-library/jest-dom ships its own `declare module 'vitest'` block, but
// it still declares `interface Assertion<T = any>` — the single-type-parameter
// shape Vitest 4 used. Vitest 5 widened the interface to
// `Assertion<R extends void | Promise<void> = void, T = unknown>`, and TypeScript
// only merges declarations whose type-parameter lists match. The upstream
// augmentation therefore stops merging and every `toBeInTheDocument()` and
// friends disappear from the types, while still working fine at runtime (the
// matchers are registered by the `@testing-library/jest-dom` import in
// src/test-setup.ts).
//
// Re-declare the augmentation against Vitest 5's arity until jest-dom ships a
// release that does it upstream, then delete this file.
import type { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers';

/* The two interfaces below are intentionally empty: they exist purely to merge
   jest-dom's matchers into Vitest's own declarations. */
/* eslint-disable @typescript-eslint/no-empty-object-type */
declare module 'vitest' {
  interface Assertion<R extends void | Promise<void> = void, T = unknown>
    extends TestingLibraryMatchers<T, R> {}

  interface AsymmetricMatchersContaining
    extends TestingLibraryMatchers<unknown, void> {}
}
/* eslint-enable @typescript-eslint/no-empty-object-type */
