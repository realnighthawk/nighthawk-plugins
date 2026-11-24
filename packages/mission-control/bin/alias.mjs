// Idempotency: the same repo can be registered in Claude Code under another marketplace name (e.g. from `marketplace add realnighthawk/nighthawk-plugins`), which would install the plugin twice.
// Remove those aliases (and the plugin copy from them) so one install is the only install. Pure parse of `claude plugin marketplace list`.
export function aliasMarketplaces(listOutput, keep = "mission-control-plugins") {
  const out = [];
  let name = null;
  for (const line of listOutput.split("\n")) {
    const n = line.match(/^\s*[❯>]\s*(\S+)\s*$/);
    if (n) name = n[1];
    else if (name && /Source:.*realnighthawk\/nighthawk-plugins/.test(line) && name !== keep) { out.push(name); name = null; }
  }
  return out;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const sample = `  ❯ nighthawk-plugins\n    Source: GitHub (realnighthawk/nighthawk-plugins)\n\n  ❯ mission-control-plugins\n    Source: Git (https://github.com/realnighthawk/nighthawk-plugins.git)\n\n  ❯ other\n    Source: GitHub (foo/bar)\n`;
  const got = JSON.stringify(aliasMarketplaces(sample));
  if (got !== '["nighthawk-plugins"]') { console.error("alias check failed: " + got); process.exit(1); }
  console.log("ok");
}
