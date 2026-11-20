#!/usr/bin/env node
/**
 * Install the Agent Skills into ~/.agents/skills.
 *
 *   npx @nighthawklabs/cookbook
 *   npx @nighthawklabs/cookbook --skills travel-planner,view-builder
 *   npx @nighthawklabs/cookbook --dry-run
 *   npx @nighthawklabs/cookbook --uninstall
 *
 * A skill is a directory: SKILL.md plus optional references/, scripts/ and assets/. Each client discovers it from its
 * own skills directory; this package only places the files.
 */
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const pkg = JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8'));
const opts = parseArgs(process.argv.slice(2));
if (opts.help) {
  usage();
  process.exit(0);
}

const skillsRoot = join(ROOT, 'skills');
const available = readdirSync(skillsRoot)
  .filter((name) => existsSync(join(skillsRoot, name, 'SKILL.md')))
  .sort();
if (opts.list) {
  console.log(available.join('\n'));
  process.exit(0);
}

const chosen = opts.skills ? opts.skills.split(',').map((s) => s.trim()).filter(Boolean) : available;
const unknown = chosen.filter((name) => !available.includes(name));
if (unknown.length) {
  console.error(`unknown skill(s): ${unknown.join(', ')}\navailable: ${available.join(', ')}`);
  process.exit(1);
}

const agentsSkills = join(opts.home, '.agents', 'skills');
const manifest = join(opts.home, '.agents', '.nighthawk-skills.json');
const installed = [];

if (opts.uninstall) {
  uninstall(chosen);
  process.exit(0);
}

for (const name of chosen) {
  const src = join(skillsRoot, name);
  const target = join(agentsSkills, name);
  const marker = join(target, '.nighthawk-skill.json');
  const ours = existsSync(marker);
  if (existsSync(target) && !ours && !opts.force) {
    console.warn(`skip ${name}: ${target} exists and was not installed by this package (use --force to replace)`);
    continue;
  }
  if (opts.dryRun) {
    console.log(`would install ${name} -> ${target}`);
  } else {
    if (existsSync(target)) rmSync(target, { recursive: true, force: true });
    mkdirSync(target, { recursive: true });
    cpSync(src, target, { recursive: true, filter: skipPycache });
    writeFileSync(marker, JSON.stringify({ source: pkg.name, version: pkg.version, installedAt: new Date().toISOString() }, null, 1) + '\n');
  }
  installed.push(name);
}

if (opts.dryRun) {
  console.log(`would install ${installed.length} skill(s) into ${agentsSkills}`);
  process.exit(0);
}

mkdirSync(join(opts.home, '.agents'), { recursive: true });
writeFileSync(
  manifest,
  JSON.stringify({ source: pkg.name, version: pkg.version, installedAt: new Date().toISOString(), skills: installed }, null, 1) + '\n',
);
console.log(`installed ${installed.length} skill(s) into ${agentsSkills}`);

function uninstall(names) {
  let removed = 0;
  for (const name of names) {
    const target = join(agentsSkills, name);
    if (!existsSync(join(target, '.nighthawk-skill.json'))) {
      console.warn(`skip ${name}: not installed by this package`);
      continue;
    }
    if (opts.dryRun) console.log(`would remove ${target}`);
    else rmSync(target, { recursive: true, force: true });
    removed += 1;
  }

  const remaining = available.filter((name) => existsSync(join(agentsSkills, name, '.nighthawk-skill.json')));
  if (!opts.dryRun) {
    if (existsSync(manifest)) {
      try {
        const data = JSON.parse(readFileSync(manifest, 'utf8'));
        data.skills = (data.skills || []).filter((name) => !names.includes(name));
        if (data.skills.length) writeFileSync(manifest, JSON.stringify(data, null, 1) + '\n');
        else rmSync(manifest, { force: true });
      } catch {
        rmSync(manifest, { force: true });
      }
    }
    if (!remaining.length) rmSync(manifest, { force: true });
  }
  console.log(`${opts.dryRun ? 'would uninstall' : 'uninstalled'} ${removed} skill(s)`);
}

function skipPycache(src) {
  return !src.split(/[\\/]/).includes('__pycache__');
}

function parseArgs(args) {
  const out = { home: homedir(), dryRun: false, force: false, list: false, uninstall: false, help: false };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === '--skills') out.skills = args[++i];
    else if (arg === '--home') out.home = resolve(args[++i]);
    else if (arg === '--dry-run') out.dryRun = true;
    else if (arg === '--force') out.force = true;
    else if (arg === '--list') out.list = true;
    else if (arg === '--uninstall') out.uninstall = true;
    else if (arg === '--help' || arg === '-h') out.help = true;
    else {
      console.error(`unknown option: ${arg}`);
      process.exit(2);
    }
  }
  return out;
}

function usage() {
  console.log(`Usage: nighthawk-cookbook [options]

Installs the Agent Skills into ~/.agents/skills.

  --skills a,b     install only these (default: every skill)
  --home DIR       install under DIR instead of $HOME (testing)
  --dry-run        print what would happen, change nothing
  --force          replace a skill directory this package did not install
  --list           list the skills and exit
  --uninstall      remove the skills this package installed`);
}
