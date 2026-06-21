import '@testing-library/jest-dom';

// PERF-04: production builds dynamic-import KaTeX from `<RichContent>` only
// when the text contains math. Tests assume the sync renderer is ready, so we
// preload KaTeX here once before any test runs.
import katex from 'katex';
import { setKatex } from './shared/ui/renderRichContent';
setKatex(katex);
