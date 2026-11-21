# CI job patterns

Replace `<runner>` with the runner the repository chose. Replace `<working-directory>` for a component in a monorepo.
These are patterns, not a universal workflow; keep only jobs the repository can run.

## Contents

- Common skeleton
- Go
- Node and TypeScript
- Python
- Swift
- Helm chart
- Service container
- Matrix
- Validation

## Common skeleton

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

jobs:
  go:
    runs-on: <runner>
    defaults:
      run:
        working-directory: <working-directory>
    steps:
      - uses: actions/checkout@v4
```

Use `defaults.run.working-directory` only when every step in the job belongs to that component.

## Go

```yaml
  go:
    runs-on: <runner>
    defaults:
      run:
        working-directory: <working-directory>
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version-file: <working-directory>/go.mod
          cache-dependency-path: <working-directory>/go.sum
      - name: Format
        run: test -z "$(gofmt -l .)"
      - name: Vet
        run: go vet ./...
      - name: Test
        run: go test -race ./...
      - name: Build
        run: go build ./...
```

Set `CGO_ENABLED=0` only when the project builds without C dependencies; do not add it by habit.

## Node and TypeScript

Detect the package manager from its lockfile and use exactly one:

```yaml
  node:
    runs-on: <runner>
    defaults:
      run:
        working-directory: <working-directory>
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: <working-directory>/.nvmrc
          cache: <pnpm|npm|yarn>
          cache-dependency-path: <working-directory>/<lockfile>
      - run: <pm> install --frozen-lockfile
      - run: <pm> run lint
      - run: <pm> run typecheck
      - run: <pm> run test
      - run: <pm> run build
```

- `pnpm`: enable with `corepack enable` before install, or use `pnpm/action-setup` pinned in the project's convention.
- `npm`: `npm ci`.
- `yarn`: `yarn install --immutable` when using Yarn Berry.
- `bun`: use the project's Bun setup action or a versioned install; do not mix lockfiles.
- Omit a script step when the script does not exist.

## Python

Prefer `uv` when the repository has `uv.lock`:

```yaml
  python:
    runs-on: <runner>
    defaults:
      run:
        working-directory: <working-directory>
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
          cache-dependency-glob: <working-directory>/uv.lock
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run pytest
```

Without `uv`, use `actions/setup-python@v5`, install from the repository's lockfile or `requirements` file, then run
the configured test and lint commands. Do not add `ruff` or `pytest` when the repository does not declare them.

## Swift

```yaml
  swift:
    runs-on: macos-latest
    defaults:
      run:
        working-directory: <working-directory>
    steps:
      - uses: actions/checkout@v4
      - run: swift build
      - run: swift test
```

Use the macOS runner version the project supports, not an arbitrary newer image. Swift CI is more expensive than Linux;
do not add an iOS archive or signing step in CI.

## Helm chart

```yaml
  helm:
    runs-on: <runner>
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v4
        with:
          version: <version>
      - run: helm lint deploy/helm/<name>
      - run: helm template <release> deploy/helm/<name> >/tmp/rendered.yaml
```

Use the repository's pinned Helm version. Chart lint does not deploy.

## Service container

Add a service only when the test suite requires it:

```yaml
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_PASSWORD: ci-only
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres -d test"
          --health-interval 2s
          --health-timeout 3s
          --health-retries 30
    env:
      TEST_DATABASE_URL: postgres://postgres:ci-only@127.0.0.1:5432/test
```

The credential is disposable and test-only; never use a production secret. The test command must create its own schema
or run the repository's migration target.

## Matrix

Matrix only real components:

```yaml
    strategy:
      fail-fast: false
      matrix:
        component: [<component-a>, <component-b>]
    defaults:
      run:
        working-directory: ${{ matrix.component }}
```

Do not make a matrix for a single component. Do not hide a failing component with `continue-on-error`.

## Validation

1. Run every job command locally, from the same directory.
2. Run `actionlint .github/workflows/ci.yml` when available.
3. Run `git diff --check`.
4. Confirm the workflow has no deploy, registry login or production secret.
5. Report `written and locally validated`; only GitHub can prove it green.
