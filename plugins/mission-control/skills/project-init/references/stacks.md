# Project scaffolds by stack

Use the stack's own initializer when available. Keep one runnable entry point and one meaningful test. Do not add a
framework or database before the brief needs it.

## Contents

- Go
- Node and TypeScript
- Python
- Swift
- Helm-only
- Multi-stack repository

## Go

Module path is normally the future repository path, `github.com/<owner>/<slug>`; ask if the owner is not fixed.

```bash
mkdir -p <slug>/cmd/<name> <slug>/internal
cd <slug>
go mod init github.com/<owner>/<slug>
```

Create:

- `cmd/<name>/main.go` with a minimal `main` that can be run.
- `internal/<name>/<name>.go` only when there is behavior worth isolating; a single `main` is enough for a small tool.
- `internal/<name>/<name>_test.go` with a test that asserts real behavior, not a tautology.
- `.gitignore` containing at least `/bin/`, `*.test`, and local coverage output.

Verify:

```bash
gofmt -w .
go vet ./...
go test ./...
go build ./...
```

Use `go.work` only for a genuine multi-module repository; do not add it to a single module.

## Node and TypeScript

Use the package manager already present in the repository, then this order when bootstrapping: `pnpm`, `npm`, `yarn`,
`bun`. Do not install a second lockfile format.

```bash
mkdir <slug>
cd <slug>
npm init -y
```

Create `src/index.ts` (or `src/index.js` when the brief does not need TypeScript), one test, `tsconfig.json` when using
TypeScript, and `.gitignore` with `node_modules/`, `dist/`, coverage and local `.env*` files except an example.

Set real scripts in `package.json`; do not leave the default test stub:

```json
{
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "<the test runner>",
    "lint": "<the linter>",
    "typecheck": "tsc -p tsconfig.json --noEmit"
  }
}
```

Use the package manager's own commands (`pnpm add`, `npm install`, ...). Verify:

```bash
<pm> install
<pm> run lint
<pm> run typecheck
<pm> run test
<pm> run build
```

If a script is not configured, omit it and write “not configured” in `AGENTS.md`; do not add a passing placeholder.

## Python

Prefer `uv` when it is installed; otherwise use the standard library and `venv`.

```bash
mkdir <slug>
cd <slug>
uv init --package --name <package>
```

Create `src/<package>/__init__.py`, one test under `tests/`, and `.gitignore` for `.venv/`, `__pycache__/`, build output
and local `.env` files. Put runtime and development dependencies in `pyproject.toml`.

Without `uv`, create `pyproject.toml`, a local virtual environment and the same source/test shape:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Verify with the tools actually declared:

```bash
uv run pytest
uv run ruff check .
uv run python -m <package>
```

Do not claim a linter, type checker or test framework that is not installed and configured.

## Swift

Use SwiftPM for a package or executable. Generate an Xcode project only when the brief explicitly asks for an app target.

```bash
mkdir <slug>
cd <slug>
swift package init --type executable
```

Create a test target with `swift package init --type executable`'s generated test support, or add one if the template
omits it. `.gitignore` must contain `.build/`, `.swiftpm/`, derived data and local Xcode user state.

Verify:

```bash
swift build
swift test
```

For an iOS app, ask for the bundle identifier, deployment target and signing strategy before generating an Xcode project;
do not invent a team or bundle id.

## Helm-only

A chart repository has no application runtime. Start from `helm create` only when a starter chart is wanted; otherwise
create the minimal structure:

```text
<slug>/
  Chart.yaml
  values.yaml
  templates/
  README.md
```

Set a real chart name, version, appVersion and description. Add one template that renders, and verify with
`helm lint .` and `helm template <release> .`. Do not add a deployment workflow here; `project-cd` owns it.

## Multi-stack repository

Use one directory per independently runnable component:

```text
<slug>/
  apps/<component>/
  services/<component>/
  packages/<component>/
  scripts/
  README.md
  AGENTS.md
```

- Each component keeps its own package manager, lockfile, tests and commands.
- The root has only cross-component scripts, documentation and repository-wide ignores.
- Do not add a root package manifest just to make one command look uniform; add a Makefile only when the person wants a
  root task runner.
- Record every component's commands separately in `AGENTS.md`.
- CI comes later and runs a matrix over the components that actually exist.
