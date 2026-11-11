# Publishing

The plugins ship as files in this public repo. There are no binaries, packages or images.

| Plugin | How it reaches users |
|---|---|
| `nighthawk-claude-code` | Claude marketplace in `.claude-plugin/marketplace.json`; bump the version in both `plugin.json` and `marketplace.json`, or cached installs keep the old one |
| `cursor` | Link or copy `plugins/cursor` into Cursor's local plugins folder |
| `codex` | `sh plugins/codex/install.sh`, then `codex mcp login hippocampus` |
| `openclaw` | `openclaw plugins install --link ./plugins/openclaw` |

## Release

Tag and create a GitHub release; there is no workflow:

```bash
git tag -a v0.4.0 -m "v0.4.0" && git push origin v0.4.0
gh release create v0.4.0 --generate-notes
```
