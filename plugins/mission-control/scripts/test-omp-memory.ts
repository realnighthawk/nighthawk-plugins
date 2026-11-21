// Run from a scratch dir whose data/retain-queue/ holds a few .txt files: bun run <this file>. A fake Hippocampus MCP stands in for the real one.
import { createServer } from "node:http";
import { existsSync } from "node:fs";
const calls: string[] = [];
const srv = createServer((req, res) => {
  let b = ""; req.on("data", (c) => (b += c)); req.on("end", () => {
    const m = JSON.parse(b);
    if (m.method === "notifications/initialized") { res.writeHead(202).end(); return; }
    const h: Record<string,string> = { "content-type": "text/event-stream" };
    let result: any = {};
    if (m.method === "initialize") { h["mcp-session-id"] = "sid1"; result = { capabilities: {} }; }
    if (m.method === "tools/call") {
      if (req.headers["mcp-session-id"] !== "sid1" || req.headers["x-agent-id"] !== "nighthawk") { res.writeHead(401).end(); return; }
      calls.push(m.params.name + ":" + (m.params.arguments.text?.length ?? m.params.arguments.query));
      result = { content: [{ type: "text", text: m.params.name === "memory_recall" ? "RECALLED-FACTS" : "ok" }] };
    }
    res.writeHead(200, h).end(`event: message\ndata: ${JSON.stringify({ jsonrpc: "2.0", id: m.id, result })}\n\n`);
  });
});
await new Promise<void>((r) => srv.listen(0, r));
process.env.MISSION_CONTROL_MEMORY_URL = `http://127.0.0.1:${(srv.address() as any).port}/mcp`;
process.env.MISSION_CONTROL_AGENT_ID = "nighthawk";
process.env.MISSION_CONTROL_DATA = process.cwd() + "/data";
const handlers: Record<string, Function> = {};
const hook = (await import(new URL("../hooks/pre/memory.ts", import.meta.url).href)).default;
hook({ on: (n: string, f: Function) => (handlers[n] = f) });
handlers.session_start({}, {});
const out = await handlers.before_agent_start({});
console.log(out.message.content);
console.log("calls", calls.join(" "));
console.log("queue left", existsSync("data/retain-queue/a.txt"), existsSync("data/retain-queue/big.txt"));
// second run injects nothing
console.log("second", await handlers.before_agent_start({}));
srv.close();
