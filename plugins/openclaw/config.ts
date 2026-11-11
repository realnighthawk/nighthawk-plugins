export type MemoryPluginConfig = {
  token: string;
  agentId: string;
  autoRecall: boolean;
  autoCapture: boolean;
  recallMinPromptLength: number;
};

/** Fixed, like the Claude Code plugin's .mcp.json: not configurable, so it cannot point at a stale or wrong server. */
export const MEMORY_MCP_URL = "https://api.nighthawklabs.org/memory/mcp";

export function parseConfig(raw: Record<string, unknown> | undefined): MemoryPluginConfig {
  const c = raw ?? {};
  const token = pickString(c.token, process.env.MISSION_CONTROL_MCP_TOKEN);
  if (!token) {
    throw new Error("mission-control: plugins.entries.mission-control.config.token (or MISSION_CONTROL_MCP_TOKEN) is required");
  }
  const agentId = pickString(c.agentId, process.env.MISSION_CONTROL_AGENT_ID) ?? "openclaw";
  return {
    token,
    // One agent for this client. Memory records it as the speaker; it is not derived per session.
    agentId,
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
