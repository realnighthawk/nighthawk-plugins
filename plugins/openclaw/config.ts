export type MemoryPluginConfig = {
  url: string;
  token: string;
  agentId: string;
  bank: string;
  autoRecall: boolean;
  autoCapture: boolean;
  recallMinPromptLength: number;
};

const DEFAULT_URL = "https://api.nighthawklabs.org/memory/mcp";

export function parseConfig(raw: Record<string, unknown> | undefined): MemoryPluginConfig {
  const c = raw ?? {};
  const token = pickString(c.token, process.env.NIGHTHAWK_MCP_TOKEN);
  if (!token) {
    throw new Error("nighthawk-memory: plugins.entries.nighthawk-memory.config.token (or NIGHTHAWK_MCP_TOKEN) is required");
  }
  return {
    url: pickString(c.url, process.env.NIGHTHAWK_MCP_URL) ?? DEFAULT_URL,
    token,
    // One agent for this client. Memory records it as the speaker; it is not derived per session.
    agentId: pickString(c.agentId, process.env.NIGHTHAWK_AGENT_ID) ?? "openclaw",
    // The server pins the bank, so this is only a label the tools require.
    bank: pickString(c.bank, process.env.NIGHTHAWK_BANK) ?? "nighthawk",
    autoRecall: bool(c.autoRecall, true),
    autoCapture: bool(c.autoCapture, true),
    recallMinPromptLength: num(c.recallMinPromptLength, 12),
  };
}

function pickString(...vals: unknown[]): string | undefined {
  for (const v of vals) {
    if (typeof v === "string") {
      const s = v.trim();
      if (s && !s.startsWith("${")) return s;
    }
  }
  return undefined;
}

function bool(v: unknown, d: boolean): boolean {
  return typeof v === "boolean" ? v : d;
}

function num(v: unknown, d: number): number {
  return typeof v === "number" && !Number.isNaN(v) ? v : d;
}
