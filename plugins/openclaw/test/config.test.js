import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { parseConfig } from "../config.ts";

for (const k of ["NIGHTHAWK_MCP_URL", "NIGHTHAWK_AGENT_ID", "NIGHTHAWK_BANK"]) delete process.env[k];

describe("parseConfig", () => {
  it("requires a token", () => {
    const saved = process.env.NIGHTHAWK_MCP_TOKEN;
    delete process.env.NIGHTHAWK_MCP_TOKEN;
    assert.throws(() => parseConfig({}));
    if (saved) process.env.NIGHTHAWK_MCP_TOKEN = saved;
  });

  it("defaults to the hosted memory MCP, one agent, one bank label", () => {
    const c = parseConfig({ token: "t.abc" });
    assert.equal(c.url, "https://api.nighthawklabs.org/memory/mcp");
    assert.equal(c.agentId, "openclaw");
    assert.equal(c.bank, "nighthawk");
    assert.equal(c.autoRecall, true);
  });

  it("ignores unexpanded ${VAR} placeholders", () => {
    assert.equal(parseConfig({ token: "t.abc", url: "${NIGHTHAWK_MCP_URL}" }).url, "https://api.nighthawklabs.org/memory/mcp");
  });
});
