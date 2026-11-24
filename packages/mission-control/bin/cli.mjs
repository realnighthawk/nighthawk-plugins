#!/usr/bin/env node
// npx @nighthawklabs/mission-control — set up Mission Control for every harness found (Claude Code, oh-my-pi), then start with `mc claude` or `mc omp`.
// It runs the bundled mc/install.sh against the bundled mc (MC_SRC=file://...), so the starter matches this package's version. No dependencies.
// ponytail: POSIX only (the starter is a shell script); a Node port of mc is the upgrade for Windows.
import { spawnSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const argv = process.argv.slice(2);
const known = ["install", "update", "uninstall", "status", "login"];
const cmd = known.includes(argv[0]) ? argv[0] : "install";
const args = argv.filter((a) => a !== cmd || argv.indexOf(a) !== 0);
if (args.includes("--help") || args.includes("-h") || (argv[0] && !argv[0].startsWith("-") && !known.includes(argv[0]))) {
  const bad = argv[0] && !argv[0].startsWith("-") && !known.includes(argv[0]);
  console.log(`${bad ? `mission-control: unknown command "${argv[0]}"\n\n` : ""}mission-control [install] [--no-login]   install mc and the plugin in Claude Code and oh-my-pi (whichever are installed), then sign in
mission-control update [--no-login]      the same again: refreshes the plugin and mc to this version
mission-control uninstall [--purge]      remove the plugin from both and mc (--purge also removes your sign-in; websocat is left alone)
mission-control status                   is the workstation reachable
mission-control login                    sign in again

Then run:  mc claude   or   mc omp
For any other agent that reads skills, install also runs npx @nighthawklabs/cookbook.`);
  process.exit(bad ? 2 : 0);
}

const sh = (c, opts = {}) => spawnSync("sh", ["-c", c], { stdio: "inherit", ...opts });
const has = (c) => spawnSync("sh", ["-c", `command -v ${c}`], { stdio: "ignore" }).status === 0;
const bin = process.env.MC_BIN_DIR || join(process.env.HOME, ".local", "bin");
const mc = join(bin, "mc");

if (process.platform === "win32") {
  console.error("mission-control: Windows is not supported yet (the starter is a POSIX shell script). Use WSL.");
  process.exit(1);
}

if (cmd === "status" || cmd === "login") {
  if (!existsSync(mc)) { console.error("mission-control: mc is not installed. Run: npx @nighthawklabs/mission-control"); process.exit(1); }
  process.exit(spawnSync(mc, [cmd], { stdio: "inherit" }).status ?? 0);
}

if (cmd === "uninstall") {
  // Both marketplace names have shipped; try each. A missing plugin is not an error.
  for (const m of ["mission-control-plugins", "nighthawk-plugins"]) {
    if (has("claude")) sh(`claude plugin uninstall mission-control@${m} --scope user 2>&1 | grep -v "not found in installed"`);
  }
  if (has("omp")) sh("omp plugin uninstall mission-control --scope user 2>&1");
  rmSync(mc, { force: true });
  if (args.includes("--purge")) rmSync(join(process.env.XDG_CONFIG_HOME || join(process.env.HOME, ".config"), "mc"), { recursive: true, force: true });
  console.log(`\nRemoved the plugin and ${mc}.${args.includes("--purge") ? "" : " Your sign-in is kept (add --purge to remove it)."} websocat was left in place.`);
  process.exit(0);
}

// install and update are the same: install.sh is safe to run again and refreshes what is there.
const root = join(dirname(fileURLToPath(import.meta.url)), "..", "mc");
const installer = join(root, "install.sh");
if (!existsSync(installer)) {
  console.error("mission-control: the bundled installer is missing (run `npm pack` from the repo, or use the published package).");
  process.exit(1);
}
const env = { ...process.env, MC_SRC: "file://" + join(root, "mc") };
if (args.includes("--no-login")) env.MC_NO_LOGIN = "1";
const run = spawnSync("sh", [installer], { stdio: "inherit", env });
if (run.status !== 0) process.exit(run.status ?? 1);

if (!has("claude") && !has("omp")) {
  console.log("\nNeither Claude Code nor oh-my-pi was found: installing the portable skills for other agents.");
  process.exit(spawnSync("npx", ["--yes", "@nighthawklabs/cookbook"], { stdio: "inherit" }).status ?? 0);
}
