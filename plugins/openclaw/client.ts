import { MEMORY_MCP_URL, type MemoryPluginConfig } from "./config.js";

/** A minimal MCP streamable-HTTP client: initialize once, then tools/call. No binary, no SDK. */
export class McpClient {
  private session: string | undefined;
  private ready: Promise<void> | undefined;
  private id = 0;
  private cfg: MemoryPluginConfig;
  private fetchImpl: typeof fetch;

  constructor(cfg: MemoryPluginConfig, fetchImpl: typeof fetch = fetch) {
    this.cfg = cfg;
    this.fetchImpl = fetchImpl;
  }

  private async post(body: Record<string, unknown>): Promise<Response> {
    const headers: Record<string, string> = {
      "content-type": "application/json",
      accept: "application/json, text/event-stream",
      authorization: `Bearer ${this.cfg.token}`,
      "x-agent-id": this.cfg.agentId,
    };
    if (this.session) headers["mcp-session-id"] = this.session;
    const res = await this.fetchImpl(MEMORY_MCP_URL, { method: "POST", headers, body: JSON.stringify(body), signal: AbortSignal.timeout(25_000) });
    if (!res.ok) throw new Error(`memory MCP ${res.status}: ${(await res.text()).slice(0, 200)}`);
    return res;
  }

  private initialize(): Promise<void> {
    this.ready ??= (async () => {
      const res = await this.post({
        jsonrpc: "2.0", id: ++this.id, method: "initialize",
        params: { protocolVersion: "2025-03-26", capabilities: {}, clientInfo: { name: "mission-control-openclaw", version: "0.2.0" } },
      });
      this.session = res.headers.get("mcp-session-id") ?? undefined;
      await parseRpc(res);
      await this.post({ jsonrpc: "2.0", method: "notifications/initialized" }).catch(() => undefined);
    })().catch((err) => {
      this.ready = undefined; // retry on the next call
      throw err;
    });
    return this.ready;
  }

  /** Calls a tool and returns its structured result (or the text content parsed as JSON when there is none). */
  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    await this.initialize();
    const res = await this.post({ jsonrpc: "2.0", id: ++this.id, method: "tools/call", params: { name, arguments: args } });
    const msg = (await parseRpc(res)) as { result?: any; error?: { message?: string } };
    if (msg.error) throw new Error(`memory MCP ${name}: ${msg.error.message ?? "error"}`);
    const result = msg.result ?? {};
    if (result.isError) throw new Error(`memory MCP ${name}: ${(result.content?.[0]?.text ?? "tool error").slice(0, 200)}`);
    if (result.structuredContent !== undefined) return result.structuredContent;
    const text = result.content?.find((c: any) => c.type === "text")?.text;
    try { return text ? JSON.parse(text) : undefined; } catch { return text; }
  }
}

/** The body is either one JSON object or an SSE stream whose `data:` event carries it. */
async function parseRpc(res: Response): Promise<unknown> {
  const text = await res.text();
  if ((res.headers.get("content-type") ?? "").includes("text/event-stream")) {
    const data = text.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim()).filter(Boolean);
    return data.length ? JSON.parse(data[data.length - 1]) : {};
  }
  return text ? JSON.parse(text) : {};
}
