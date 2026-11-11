import type { MemoryPluginConfig } from "./config.js";
import type { McpClient } from "./client.js";
import type { PluginApi } from "./recall.js";
import { loadLastUserPrompt } from "./session-state.js";

export type AgentEndCtx = {
  sessionKey?: string;
  trigger?: string;
  messages?: Array<{ role?: string; content?: string }>;
};

/** Retains the finished turn as role-prefixed lines. The server records the caller (X-Agent-ID) as the speaker. */
export function createCaptureHook(api: PluginApi, cfg: MemoryPluginConfig, client: McpClient) {
  return async (ctx: AgentEndCtx) => {
    if (ctx.trigger === "memory" || ctx.sessionKey?.includes(":memory-capture:")) return {};
    const prompt = (await loadLastUserPrompt(ctx.sessionKey).catch(() => "")).trim();
    if (!prompt) return {};

    const reply = [...(ctx.messages ?? [])].reverse().find((m) => m.role === "assistant" && m.content?.trim())?.content?.trim() ?? "";
    const text = `user: ${prompt.slice(0, 1500)}${reply ? `\n\nassistant: ${reply.slice(0, 1500)}` : ""}`;
    try {
      await client.callTool("memory_retain", { text, mention_time: new Date().toISOString() });
    } catch (err) {
      api.logger.warn(`mission-control: retain failed: ${String(err)}`);
    }
    return {};
  };
}
