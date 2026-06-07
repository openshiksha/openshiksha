#!/usr/bin/env node
/**
 * Launches Vite directly into the widget dev playground.
 *
 * Usage:
 *   npm run widget:dev
 *   npm run widget:dev -- number-line
 */

import { spawn } from 'node:child_process';

const kind = process.argv[2];
const path = kind ? `/widgets/dev?kind=${encodeURIComponent(kind)}` : '/widgets/dev';
const viteBin = process.platform === 'win32' ? 'vite.cmd' : 'vite';

const child = spawn(viteBin, ['--host', '0.0.0.0', '--open', path], {
  stdio: 'inherit',
  shell: process.platform === 'win32',
});

child.on('exit', (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  process.exit(code ?? 0);
});
