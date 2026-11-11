import { parseConfig } from "./config.js";
import { McpClient } from "./client.js";
import { createCaptureHook } from "./capture.js";
import { createRecallHook, type PluginApi } from "./recall.js";

/** Minimal API surface — full types from openclaw/plugin-sdk at runtime. */
type OpenClawPluginApi = PluginApi & {
  id: string;
  name: string;
  description?: string;
  pluginConfig?: Record<string, unknown>;
  on: (event: string, handler: (ctx: unknown) => Promise<unknown>) => void;
};

const nighthawkMemoryPlugin = {
  id: "nighthawk-memory",
  name: "Nighthawk Memory",
  description: "Hippocampus long-term memory with automatic recall and capture",
  kind: "memory" as const,

  register(api: OpenClawPluginApi) {
    const cfg = parseConfig(api.pluginConfig);
    const client = new McpClient(cfg);
    if (cfg.autoRecall) api.on("before_prompt_build", createRecallHook(api, cfg, client) as never);
    if (cfg.autoCapture) api.on("agent_end", createCaptureHook(api, cfg, client) as never);
    api.logger.info(`nighthawk-memory: agent ${cfg.agentId}, hooks: ${[cfg.autoRecall && "before_prompt_build", cfg.autoCapture && "agent_end"].filter(Boolean).join(", ") || "(none)"}`);
  },
};

export default nighthawkMemoryPlugin;
