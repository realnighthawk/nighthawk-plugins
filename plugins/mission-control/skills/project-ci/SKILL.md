---
name: project-ci
description: Adds or repairs a repository's GitHub Actions CI checks: detects the stacks and their real commands, writes lint, typecheck, test and build jobs, validates them locally, and leaves deployment alone. Use when a project needs CI, a workflow is missing or red, a stack changes, or the person asks for automated checks. Not for creating a repository or deploying; use project-init and project-cd.
---

# Add CI

CI proves what the repository already claims. Read the project, use the commands its maintainers use, and keep the
workflow small enough to debug. This skill never builds an image for release, never deploys, and never handles secrets
for a deployment.

## 1. Read the project

Read `AGENTS.md`, `README.md`, existing workflows and the package/stack files before writing:

```bash
git status --short --branch
find .github/workflows -maxdepth 1 -type f 2>/dev/null
rg --files -g 'go.mod' -g 'package.json' -g 'pnpm-lock.yaml' -g 'package-lock.json' -g 'yarn.lock' -g 'bun.lock*'
rg --files -g 'pyproject.toml' -g 'uv.lock' -g 'requirements*.txt' -g 'Package.swift' -g 'Chart.yaml'
```

- There is at least one stack: detect it from files, not from the repository name.
- There is exactly one package manager per component; use its lockfile.
- An existing workflow is read in full. Improve it unless it is unrelated; never silently replace another workflow.
- A command written in `AGENTS.md` is a claim until you run it. Fix the claim or the command.

## 2. Make the CI plan

Write this before generating YAML:

```text
Repository: <name>
Components: <path -> stack -> package manager>
Checks: <path -> lint/typecheck/test/build commands>
Runner: <labels or hosted image, chosen by the person>
Services: <database/browser/etc, or none>
Artifacts: <coverage/test report, or none>
Not in CI: build image, publish, deploy
```

Runner choice is per repository. Do not copy `runs-on` from another project and do not assume a self-hosted runner.
Ask when the brief does not name one. Record the answer in `AGENTS.md` so later runs do not guess.

## 3. Use the real commands

Load [references/workflows.md](references/workflows.md) for stack-specific setup and job templates.

- A command belongs in CI only when it exists and passes locally.
- Do not add a new linter, test framework or type checker just to fill a job. Add it to the project first, with its
  configuration and dependencies, then wire CI.
- A missing command is reported as **not configured**, not replaced by `true`, `echo`, or a passing placeholder.
- One job per independently runnable component. A single-component repository gets one job unless lint/test/build need
  different services.
- Use caching only where the stack's setup action supports it and the cache key uses the lockfile.
- Use a service container only when the tests actually require it; name the health check and the timeout reason.

## 4. Write `.github/workflows/ci.yml`

Keep these invariants:

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

- Jobs use the chosen runner, no unreviewed self-hosted label.
- Pin actions by the repository's convention; start with the major version (`actions/checkout@v4`) unless the project
  already pins by SHA.
- Do not put secrets in CI unless the checks genuinely need them. A CI check that needs a production secret is the wrong
  check.
- Do not add `pull_request_target`.
- Matrix only the components that exist; do not invent an empty matrix.
- Upload artifacts only when they are useful to a failure (coverage, test report), never as a default.

## 5. Validate locally

Run the workflow commands in the same order from the repository root. Then validate the YAML:

```bash
actionlint .github/workflows/ci.yml   # when actionlint is installed
git diff --check
```

If `actionlint` is not installed, say so and validate the workflow structure against the reference; do not install a
global tool silently. A workflow that has not been run on GitHub is reported as **written and locally validated**, not
as green.

## 6. Finish

- Commit only the CI changes and any `AGENTS.md` command corrections.
- Push when the repository has a remote and the person asked to add CI. Never force-push.
- Report the workflow path, the jobs and commands, the runner, the local validation, and anything still unverified.
- If the next need is release/deploy, hand off to `project-cd`; do not add it here.
