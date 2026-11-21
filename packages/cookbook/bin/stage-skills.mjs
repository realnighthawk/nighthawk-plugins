#!/usr/bin/env node
/**
 * Stage the portable skills from the plugin into the npm package.
 *
 * The plugin is the source of truth. This copies its portable skills into `packages/cookbook/skills` so the tarball
 * is self-contained. It runs at `prepack` and at the start of `make check`; the staged directory is gitignored.
 */
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const SOURCE = resolve(ROOT, '..', '..', 'plugins', 'mission-control', 'skills');
const TARGET = join(ROOT, 'skills');
const PLUGIN_ONLY = new Set(['hippocampus', 'services']);

if (!existsSync(SOURCE)) {
  console.error(`source skills not found: ${SOURCE}`);
  process.exit(1);
}
const portable = readdirSync(SOURCE)
  .filter((name) => existsSync(join(SOURCE, name, 'SKILL.md')) && !PLUGIN_ONLY.has(name))
  .sort();
if (!portable.length) {
  console.error(`no portable skills under ${SOURCE}`);
  process.exit(1);
}

rmSync(TARGET, { recursive: true, force: true });
mkdirSync(TARGET, { recursive: true });
for (const name of portable) {
  cpSync(join(SOURCE, name), join(TARGET, name), {
    recursive: true,
    filter: (path) => !path.split(/[\\/]/).includes('__pycache__'),
  });
}
console.log(`staged ${portable.length} skills into ${TARGET}`);
