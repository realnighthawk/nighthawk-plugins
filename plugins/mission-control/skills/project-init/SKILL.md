---
name: project-init
description: Plans and scaffolds a new software project: chooses the stack and layout, creates the directory, initializes git, writes README.md and AGENTS.md, runs local checks, and optionally creates a GitHub repository. Use when starting a project, bootstrapping a repo, adopting an unversioned directory, or asking to set up a new app, service, library or package. Not for adding CI or deployment; use project-ci and project-cd.
---

# Start a project

A project starts with a small, testable foundation, not a pile of generated folders. Inspect before writing, keep the
scaffold minimal, verify the commands you document, and create the remote only after the local repository is sound.

This skill does not create CI or deployment. Stop before those; `project-ci` and `project-cd` own them.

## 1. Ask only what changes the files

Ask these together, once:

- **Name and purpose** — the directory slug, one sentence on what it does, and who uses it.
- **Location** — default `~/projects/<slug>`; use another path only when the person names one.
- **Stack** — one or more of Go, Node/TypeScript, Python, Swift/iOS, Helm-only; ask when the brief does not name one.
- **Existing directory** — if it already exists, inspect it first and ask before changing anything.
- **GitHub** — owner (personal account or organisation), visibility, and whether to create the remote now.
- **License** — only if the person asks; never guess a license.

If the person asks for several stacks, plan one repository with each stack in its own directory unless they ask for
separate repositories.

## 2. Inspect before writing

Check the destination, git state, available tools and GitHub login:

```bash
pwd
ls -la <destination>
git -C <destination> status --short --branch
git --version
gh --version
gh auth status
```

- A non-empty directory is never overwritten. Inspect it, report what is already there, and ask whether to adopt it.
- `git status` inside an existing repository means adopt, not re-initialize.
- If `gh` is missing or signed out, continue with a local git repository only if the person agrees; stop before any
  remote step and say **“Connect GitHub in Agent setup, then return here.”** Do not ask for a token.
- Never read or print a credential.

## 3. Plan before scaffolding

Write a short plan in the conversation and use it as the README draft:

```text
Kind: <app | service | library | CLI | package | chart>
Purpose: <one sentence>
Stack(s): <names and versions the project actually uses>
Layout: <top-level directories and why>
Commands: <install | run | test | lint | build>
Verification: <tooling installs and manifests parse; no application behavior yet>
Remote: <owner/repo | none>, <private/public>, <create now | later>
Not now: application code, tests, CI, deployment, secrets
```

If two stacks share a root, name which commands belong to which directory. If a choice is still unknown, mark it
unknown instead of inventing it.

## 4. Scaffold an empty project shell

Create the directory, manifests and tooling. Do **not** create application source, routes, handlers, sample business
logic, or tests; the coding tasks own those and their verification. Details and file shapes:
[references/stacks.md](references/stacks.md).

- Go: initialize the module and the intended directories, but no `main` or test file.
- Node/TypeScript: initialize the package manager and manifest, but no source entry or test.
- Python: create `pyproject.toml` and the virtual environment/tooling, but no module or test.
- Swift: create `Package.swift` and empty target directories, but no source or test.
- Helm-only: create the chart skeleton and a README; there is no application source.
- Multiple stacks: scaffold each in its own directory; do not merge package managers.

Add only repository shell and tooling:

- `.gitignore` for the chosen stack and local tooling.
- `.editorconfig` when the stack has no formatter-owned config and the person did not object.
- `README.md` with purpose, requirements, layout and the current command status.
- `AGENTS.md` with the working context below.
- Empty source/test directories need a tracked placeholder such as `.gitkeep`; do not add fake code.
- No CI, no deployment manifests, no secrets, no generated sample domains.

Do not write a test that asserts nothing, a placeholder `main`, or a “hello world” route just to claim verification.

### README.md

Keep it short and executable. It must contain:

- what the project is and who it is for;
- prerequisites with versions that matter;
- install command that you have run;
- run, test, lint and build marked **not configured until the application code exists**;
- the directory layout and the empty source/test directories;
- the planned deployment target, marked as **not configured** until `project-cd` adds it.

### AGENTS.md

Write it for the next agent, not for a marketing page:

```md
# Project
<one paragraph: purpose and users>

## Stack
<language/runtime/package manager and versions>

## Layout
<directory: responsibility>

## Commands
- Install: <verified command>
- Run: not configured until application code exists
- Test: not configured until application code exists
- Lint: not configured until application code exists
- Build: not configured until application code exists

## Conventions
<only invariants the shell/tooling establishes; no invented app behavior>

## Delivery
Container + Helm planned; not configured. CI and CD are separate skills.
```

The coding tasks update these commands when they add behavior. Do not mark a command configured before it runs.

## 5. Verify the shell and tooling

Run only the commands that exist: dependency installation and manifest/config parsing. Do not run an application build,
test suite or lint over no source and call it verification.

Then inspect the repository before committing:

```bash
git -C <destination> status --short
git -C <destination> diff --check
rg --files -g '.env*' -g '*secret*' -g '*credential*' -g '*token*' -g '*.pem' <destination>
```

Fix the scaffold before making the first commit. Do not commit generated dependency directories, build output or local
environment files.

## 6. Initialize git with the person's identity

```bash
cd <destination>
git init -b main
login=$(gh api user --jq .login)
id=$(gh api user --jq .id)
name=$(gh api user --jq '.name // .login')
git config user.name "$name"
git config user.email "${id}+${login}@users.noreply.github.com"
```

This is repository-local configuration; do not change the person's global git identity. If GitHub is not connected, use
the identity the person gives you instead of inventing one, or stop before the commit.

Stage only the scaffold and make one initial commit:

```bash
git add .gitignore README.md AGENTS.md <source and test paths>
git commit -m "Initialize <slug>"
```

Verify with `git show --stat --oneline HEAD`.

## 7. Create the remote only when asked

Ask the owner and visibility every time; do not reuse the last project's owner. List the choices if needed:

```bash
gh api user --jq .login
gh api user/orgs --jq '.[].login'
```

Create the repository from the existing local source, never by re-initializing over it:

```bash
gh repo create <owner>/<slug> --private --source . --remote origin --push
```

Use `--public` only when the person chose public. If the remote already exists, stop and report it; never force-push.
If creation fails after the local commit, leave the local repository intact and report the exact error.

## 8. Report

State:

- the path, stack, tooling install command and what was verified;
- that no application code or tests exist yet;
- the initial commit hash;
- the repository URL, or exactly why no remote was created;
- what is deliberately absent: code, tests, CI, deployment, secrets;
- the next step: a coding task, then `project-ci` once there are runnable checks.

Do not claim a command passed unless you ran it. Do not report a remote that was not created.
