import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { parseConfig, MEMORY_MCP_URL } from "../config.ts";

for (const k of ["NIGHTHAWK_MCP_URL", "NIGHTHAWK_AGENT_ID", "NIGHTHAWK_BANK"]) delete process.env[k];

describe("parseConfig", () => {
  it("requires a token", () => {
    const saved = process.env.NIGHTHAWK_MCP_TOKEN;
    delete process.env.NIGHTHAWK_MCP_TOKEN;
    assert.throws(() => parseConfig({}));
    if (saved) process.env.NIGHTHAWK_MCP_TOKEN = saved;
  });

  it("defaults to one agent and one bank label; the endpoint is fixed", () => {
    const c = parseConfig({ token: "t.abc", url: "http://elsewhere/mcp" });
    assert.equal(MEMORY_MCP_URL, "https://api.nighthawklabs.org/memory/mcp");
    assert.equal("url" in c, false, "no url override");
    assert.equal(c.agentId, "openclaw");
    assert.equal(c.bank, "nighthawk");
    assert.equal(c.autoRecall, true);
  });
});
