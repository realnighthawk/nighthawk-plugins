#!/usr/bin/env node
/**
 * Stage the portable skills from the plugins into the npm package.
 *
 * The plugins are the source of truth. This copies their portable skills into `packages/cookbook/skills` so the tarball
 * is self-contained. It runs at `prepack` and at the start of `make check`; the staged directory is gitignored.
 */
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const PLUGINS = resolve(ROOT, '..', '..', 'plugins');
const SOURCES = existsSync(PLUGINS)
  ? readdirSync(PLUGINS).map((p) => join(PLUGINS, p, 'skills')).filter((d) => existsSync(d))
  : [];
const TARGET = join(ROOT, 'skills');
const PLUGIN_ONLY = new Set(['hippocampus', 'services']);

const portable = SOURCES.flatMap((dir) =>
  readdirSync(dir)
    .filter((name) => existsSync(join(dir, name, 'SKILL.md')) && !PLUGIN_ONLY.has(name))
    .map((name) => [name, join(dir, name)]),
).sort(([a], [b]) => a.localeCompare(b));
if (!portable.length) {
  console.error(`no portable skills under ${PLUGINS}`);
  process.exit(1);
}

rmSync(TARGET, { recursive: true, force: true });
mkdirSync(TARGET, { recursive: true });
for (const [name, src] of portable) {
  cpSync(src, join(TARGET, name), {
    recursive: true,
    filter: (path) => !path.split(/[\\/]/).includes('__pycache__'),
  });
}
console.log(`staged ${portable.length} skills into ${TARGET}`);
