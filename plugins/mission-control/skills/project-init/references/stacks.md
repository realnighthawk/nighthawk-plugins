# Project shells by stack

A project shell has a package manifest, directory layout and tooling, with **no application source or tests**. The coding
tasks add source and tests, then update `AGENTS.md` and verify them.

Use the package manager already present in the repository. Do not add a second lockfile format, framework, linter or test
runner just to make the shell look complete.

## Contents

- Go
- Node and TypeScript
- Python
- Swift
- Helm-only
- Multi-stack repository

## Common shell

```text
<slug>/
  .editorconfig
  .gitignore
  README.md
  AGENTS.md
```

Track empty directories with `.gitkeep`; never add a placeholder `main`, route, handler or test.

## Go

```bash
mkdir -p <slug>/cmd/<name> <slug>/internal
cd <slug>
go mod init github.com/<owner>/<slug>
touch cmd/<name>/.gitkeep internal/.gitkeep
```

Create `.gitignore` with `/bin/`, `*.test`, coverage output and local environment files.

Verify only the module and formatting tool:

```bash
go env GOMOD
gofmt -l .
```

Do not create `main.go` or a test file. The coding task owns the first command package and its tests.

## Node and TypeScript

Use the package manager already present, then this order when bootstrapping: `pnpm`, `npm`, `yarn`, `bun`.

```bash
mkdir -p <slug>/src <slug>/test
cd <slug>
<pm> init
touch src/.gitkeep test/.gitkeep
```

Set `private: true` for an application, the real package name, the package manager field, and no fake scripts. Tooling
configuration may be added when the coding task chooses a framework or test runner; do not install a framework in init.

`.gitignore` must contain `node_modules/`, build output, coverage and local `.env*` files except an example.

Verify:

```bash
<pm> install
node -e 'JSON.parse(require("fs").readFileSync("package.json", "utf8"))'
```

Do not add a `hello world` entry, a test stub or a passing placeholder script.

## Python

Prefer `uv` when installed; otherwise use a local virtual environment and `pyproject.toml`.

```bash
mkdir -p <slug>/src <slug>/tests
cd <slug>
uv init --bare
touch src/.gitkeep tests/.gitkeep
```

`uv init --bare` creates the manifest/workspace shell without a package source file. Declare the supported Python
version and the build backend. Add linter/test dependencies only when the coding task chooses them.

`.gitignore` must contain `.venv/`, `__pycache__/`, build output and local `.env` files.

Verify:

```bash
uv sync
uv run python -c 'import tomllib, pathlib; tomllib.loads(pathlib.Path("pyproject.toml").read_text())'
```

Without `uv`, create the same manifest and a local `.venv`; install only declared tooling, not an invented framework.

## Swift

Create the package manifest and empty target directories manually; do not let `swift package init` write sample source
or tests.

```bash
mkdir -p <slug>/Sources/<name> <slug>/Tests/<name>Tests
cd <slug>
touch Sources/<name>/.gitkeep Tests/<name>Tests/.gitkeep
```

Create `Package.swift` with the real package name, platforms, products, targets and test target. Keep the targets
empty. `.gitignore` must contain `.build/`, `.swiftpm/`, derived data and local Xcode user state.

Verify only that the manifest parses:

```bash
swift package dump-package >/dev/null
```

Do not run `swift build` or `swift test` over empty targets and call that application verification.

For an iOS app, ask for the bundle identifier, deployment target and signing strategy before generating an Xcode project;
do not invent a team or bundle id.

## Helm-only

A chart repository has no application runtime. Create the minimal structure:

```text
<slug>/
  Chart.yaml
  values.yaml
  templates/
  README.md
```

Set a real chart name, version, appVersion and description. Add one template only if it is meaningful; an empty chart
skeleton is acceptable for init. Verify with `helm lint .` and `helm template <release> .`.

Do not add a deployment workflow here; `project-cd` owns it.

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

- Each component keeps its own package manager, lockfile and empty source/test directories.
- The root has only cross-component documentation and repository-wide ignores.
- Do not add a root package manifest just to make one command look uniform; add a Makefile only when the person wants a
  root task runner.
- Record every component's install command and the fact that run/test/lint/build are not configured in `AGENTS.md`.
- CI comes after the coding tasks create runnable checks.
