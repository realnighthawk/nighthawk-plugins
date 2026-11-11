import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { McpClient } from "../client.ts";
import { formatRecallBlock } from "../format.ts";
import { createCaptureHook } from "../capture.ts";
import { createRecallHook } from "../recall.ts";
import { parseConfig } from "../config.ts";

for (const k of ["NIGHTHAWK_MCP_URL", "NIGHTHAWK_AGENT_ID", "NIGHTHAWK_BANK"]) delete process.env[k];
const cfg = parseConfig({ token: "tenant.mac" });
const logger = { info() {}, warn() {} };

/** A fake MCP server: records every request, answers initialize (with a session id), tools/call as JSON or SSE. */
function fakeServer(toolResult, { sse = false } = {}) {
  const seen = [];
  const fetchImpl = async (url, init) => {
    const body = JSON.parse(init.body);
    seen.push({ url, headers: init.headers, body });
    const reply = (obj, extra = {}) => {
      const text = sse ? `event: message\ndata: ${JSON.stringify(obj)}\n\n` : JSON.stringify(obj);
      return new Response(text, { status: 200, headers: { "content-type": sse ? "text/event-stream" : "application/json", ...extra } });
    };
    if (body.method === "initialize") return reply({ jsonrpc: "2.0", id: body.id, result: {} }, { "mcp-session-id": "sess-1" });
    if (body.method === "notifications/initialized") return new Response(null, { status: 202 });
    return reply({ jsonrpc: "2.0", id: body.id, result: { structuredContent: toolResult } });
  };
  return { fetchImpl, seen };
}

describe("McpClient", () => {
  it("initializes once, then sends bearer, agent id and session on each call", async () => {
    const { fetchImpl, seen } = fakeServer({ results: [] });
    const client = new McpClient(cfg, fetchImpl);
    await client.callTool("memory_recall", { bank_id: "nighthawk", query: "x" });
    await client.callTool("memory_recall", { bank_id: "nighthawk", query: "y" });
    assert.equal(seen[0].url, "https://api.nighthawklabs.org/memory/mcp");
    assert.deepEqual(seen.map((s) => s.body.method), ["initialize", "notifications/initialized", "tools/call", "tools/call"]);
    const call = seen[3];
    assert.equal(call.headers.authorization, "Bearer tenant.mac");
    assert.equal(call.headers["x-agent-id"], "openclaw");
    assert.equal(call.headers["mcp-session-id"], "sess-1");
    assert.deepEqual(call.body.params, { name: "memory_recall", arguments: { bank_id: "nighthawk", query: "y" } });
  });

  it("reads an SSE reply", async () => {
    const { fetchImpl } = fakeServer({ ok: 1 }, { sse: true });
    assert.deepEqual(await new McpClient(cfg, fetchImpl).callTool("t", {}), { ok: 1 });
  });

  it("raises on a tool error and on HTTP errors", async () => {
    const bad = async (url, init) => {
      const b = JSON.parse(init.body);
      if (b.method === "initialize") return new Response(JSON.stringify({ result: {} }), { status: 200, headers: { "content-type": "application/json" } });
      if (b.method === "notifications/initialized") return new Response(null, { status: 202 });
      return new Response(JSON.stringify({ result: { isError: true, content: [{ type: "text", text: "boom" }] } }), { status: 200, headers: { "content-type": "application/json" } });
    };
    await assert.rejects(new McpClient(cfg, bad).callTool("t", {}), /boom/);
    await assert.rejects(new McpClient(cfg, async () => new Response("no", { status: 401 })).callTool("t", {}), /401/);
  });
});

describe("hooks", () => {
  it("recall prepends the recalled memory", async () => {
    const { fetchImpl, seen } = fakeServer({ results: [{ text: "The user prefers short answers.", mention_time: "2026-11-01T00:00:00Z" }] });
    const out = await createRecallHook({ logger }, cfg, new McpClient(cfg, fetchImpl))({ prompt: "how should you answer me?", sessionKey: "s1" });
    assert.match(out.prependContext, /The user prefers short answers\. \(2026-11-01\)/);
    assert.equal(seen.at(-1).body.params.arguments.bank_id, "nighthawk");
  });

  it("recall fails open", async () => {
    const out = await createRecallHook({ logger }, cfg, new McpClient(cfg, async () => new Response("x", { status: 500 })))({ prompt: "a long enough prompt", sessionKey: "s2" });
    assert.deepEqual(out, {});
  });

  it("capture retains the turn as role-prefixed lines", async () => {
    const { fetchImpl, seen } = fakeServer({ status: "accepted" });
    const client = new McpClient(cfg, fetchImpl);
    await createRecallHook({ logger }, cfg, client)({ prompt: "remember that I deploy on Fridays", sessionKey: "s3" });
    await createCaptureHook({ logger }, cfg, client)({ sessionKey: "s3", messages: [{ role: "assistant", content: "Noted." }] });
    const retain = seen.filter((s) => s.body.method === "tools/call").at(-1).body.params;
    assert.equal(retain.name, "memory_retain");
    assert.equal(retain.arguments.text, "user: remember that I deploy on Fridays\n\nassistant: Noted.");
  });

  it("formatRecallBlock is empty with no results", () => {
    assert.equal(formatRecallBlock({ results: [] }), "");
  });
});
