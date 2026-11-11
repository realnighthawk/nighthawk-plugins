# Publishing

The plugins ship as files in this public repo. Nothing is published to npm or GHCR.

| Plugin | How it reaches users |
|---|---|
| `nighthawk-claude-code` | Claude marketplace in `.claude-plugin/marketplace.json`; bump the version in both `plugin.json` and `marketplace.json`, or cached installs keep the old one |
| `cursor` | Link or copy `plugins/cursor` into Cursor's local plugins folder |
| `codex` | `sh plugins/codex/install.sh`, then `codex mcp login hippocampus` |
| `openclaw` | `openclaw plugins install --link ./plugins/openclaw` |
| `claude-code` (legacy) | Its hook binary, `agent-brain-hook`, is downloaded from the latest GitHub release |

## Release

Push a `v*` tag. The workflow in `.github/workflows/publish.yml` builds `agent-brain-hook` for linux/darwin amd64/arm64 plus `checksums.txt` and attaches them to the GitHub release for that tag.

```bash
git tag -a v0.3.0 -m "v0.3.0"
git push origin v0.3.0
```
