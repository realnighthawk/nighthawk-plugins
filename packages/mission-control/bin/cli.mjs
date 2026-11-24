#!/usr/bin/env node
// npx @nighthawklabs/mission-control — set up Mission Control for every harness found (Claude Code, oh-my-pi), then start with `mc claude` or `mc omp`.
// It runs the bundled mc/install.sh against the bundled mc (MC_SRC=file://...), so the starter matches this package's version. No dependencies.
// ponytail: POSIX only (the starter is a shell script); a Node port of mc is the upgrade for Windows.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const args = process.argv.slice(2);
if (args.includes("--help") || args.includes("-h")) {
  console.log(`mission-control [--no-login]

Installs the mc starter and the Mission Control plugin into Claude Code and oh-my-pi (whichever are installed), and signs you in.
Then run:  mc claude   or   mc omp
For any other agent that reads skills, it installs the portable skills (npx @nighthawklabs/cookbook).`);
  process.exit(0);
}

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "mc");
const installer = join(root, "install.sh");
if (!existsSync(installer)) {
  console.error("mission-control: the bundled installer is missing (run `npm pack` from the repo, or use the published package).");
  process.exit(1);
}
if (process.platform === "win32") {
  console.error("mission-control: Windows is not supported yet (the starter is a POSIX shell script). Use WSL.");
  process.exit(1);
}

const has = (cmd) => spawnSync("sh", ["-c", `command -v ${cmd}`], { stdio: "ignore" }).status === 0;
const env = { ...process.env, MC_SRC: "file://" + join(root, "mc") };
if (args.includes("--no-login")) env.MC_NO_LOGIN = "1";
const run = spawnSync("sh", [installer], { stdio: "inherit", env });
if (run.status !== 0) process.exit(run.status ?? 1);

if (!has("claude") && !has("omp")) {
  console.log("\nNeither Claude Code nor oh-my-pi was found: installing the portable skills for other agents.");
  process.exit(spawnSync("npx", ["--yes", "@nighthawklabs/cookbook"], { stdio: "inherit" }).status ?? 0);
}
