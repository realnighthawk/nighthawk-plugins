---
name: workspace
description: How to work in the agent's sandbox: where projects live (/workspace), what persists, what the network allows, how to use git, the shell and the browser, and how to report work back. Use when a task creates, reads or changes files, runs commands, clones a repository, installs a tool, or needs to know what the sandbox can reach. Not for how to write code or structure a project.
---

# Working in the workspace

`/workspace` is this agent's persistent volume. Every project the agent works on is a directory in it: `/workspace/<project>`.
It survives restarts and sleep. The session directory is scratch; the harness's home volume holds its own config and
logins. Neither is a place for projects, and the logins are never read, copied or printed.

## Start

```bash
test -d /workspace && ls -la /workspace
```

- If `/workspace` is missing, say the workspace is not mounted and stop file work. Do not put a project in the session
  directory instead; it would look saved and not be.
- If the project exists, resume it: `git status --short --branch`, read its `AGENTS.md`, then continue. Clone or create
  only when it is not there.
- One project, one directory. Do not nest projects, and do not write outside `/workspace/<project>` for project work.

## What the sandbox allows

- **Root is read-only; no sudo, no package manager for the system.** Install per project: a virtualenv, `node_modules`,
  a local `bin/` inside the project directory.
- **Network is HTTPS through a proxy that allows named hosts only.** There is no DNS and no SSH. Use `https://` git
  remotes. A connection failure on one host usually means it is not allowed: report the host and what needed it. Do not
  look for another route (tunnels, mirrors, other hosts).
- **Credentials:** none beyond the harness's own login. Check `gh auth status` before assuming GitHub write access, and
  never write a token into the workspace, a remote URL or a commit.
- **Browser:** for anything on a website, use the `browser` skill, not `curl`.

## Reporting back

End a task with the project path, what changed (`git status --short`, or the commit made), how it was checked and
what was not. Commit only when asked; never force-push or rewrite history that is not yours.
