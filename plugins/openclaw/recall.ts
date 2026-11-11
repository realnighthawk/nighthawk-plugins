import type { MemoryPluginConfig } from "./config.js";
import type { McpClient } from "./client.js";
import { formatRecallBlock } from "./format.js";
import { saveLastUserPrompt } from "./session-state.js";

export type PluginApi = {
  rootDir?: string;
  logger: { info: (msg: string) => void; warn: (msg: string) => void };
};

export type BeforePromptBuildCtx = { prompt?: string; sessionKey?: string; trigger?: string };

export function createRecallHook(api: PluginApi, cfg: MemoryPluginConfig, client: McpClient) {
  return async (ctx: BeforePromptBuildCtx) => {
    if (ctx.trigger === "memory") return {};
    const prompt = (ctx.prompt ?? "").trim();
    if (prompt.length < cfg.recallMinPromptLength) return {};
    await saveLastUserPrompt(ctx.sessionKey, prompt);

    const query = prompt.replace(/\s+/g, " ").slice(0, 500);
    try {
      const block = formatRecallBlock(await client.callTool("memory_recall", { query }));
      return block ? { prependContext: block } : {};
    } catch (err) {
      api.logger.warn(`nighthawk-memory: recall failed: ${String(err)}`);
      return {};
    }
  };
}
