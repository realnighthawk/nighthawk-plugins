// prepack: copy the mc starter and its installer from the repo root into the tarball, so what npx runs is the version that was published, not whatever is on main.
import { cpSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "..", "mc");
mkdirSync(out, { recursive: true });
for (const f of ["mc", "install.sh"]) cpSync(join(here, "..", "..", "..", "mc", f), join(out, f));
