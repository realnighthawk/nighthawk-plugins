/**
 * Mission Control memory hooks for oh-my-pi.
 *
 * When the process starts (session_start, before any message) the hook does the memory work itself, over the same Hippocampus MCP endpoint and
 * headers the plugin's .mcp.json names: it retains any slice the previous session spooled, then recalls. The first agent run is handed the recall
 * results as context, so the first message spends no model step on memory. At shutdown it writes a compact slice of the session to the retain
 * queue for the next start. A failure is reported to the agent in that same context (never silently skipped) and leaves the queue as it was.
 */
import type { HookAPI } from "@oh-my-pi/pi-coding-agent/extensibility/hooks";
import { mkdirSync, readdirSync, readFileSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const CAP = 120_000;
const MAX_SPOOLED = 10;
const DISABLED = Boolean(process.env.MISSION_CONTROL_DISABLE_HOOKS);

function dataDir(): string {
	return process.env.MISSION_CONTROL_DATA || join(process.env.XDG_CACHE_HOME || join(homedir(), ".cache"), "mission-control");
}

function queueDir(): string {
	return join(dataDir(), "retain-queue");
}

const RECALL_QUERY = "the user, their preferences, and what they are working on";
const CHUNK = 20_000; // one retain call's text; a slice longer than this goes in several
const CALL_TIMEOUT_MS = 20_000;
const FIRST_RUN_WAIT_MS = 15_000;

function queued(): string[] {
	try {
		return readdirSync(queueDir())
			.filter((f) => f.endsWith(".txt"))
			.slice(0, 5)
			.map((f) => join(queueDir(), f));
	} catch {
		return []; // no queue yet
	}
}

/** The Hippocampus MCP endpoint, as .mcp.json names it, over streamable HTTP: one initialize, then tool calls on that session. */
async function connect(): Promise<(tool: string, args: Record<string, unknown>) => Promise<string>> {
	const url = process.env.MISSION_CONTROL_MEMORY_URL || "https://api.nighthawklabs.org/memory/mcp";
	const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "application/json, text/event-stream" };
	if (process.env.MISSION_CONTROL_AGENT_ID) headers["X-Agent-ID"] = process.env.MISSION_CONTROL_AGENT_ID;
	if (process.env.MISSION_CONTROL_MEMORY_KEY) headers["X-API-Key"] = process.env.MISSION_CONTROL_MEMORY_KEY;
	let id = 0;
	const post = async (body: Record<string, unknown>): Promise<Response> => {
		const res = await fetch(url, { method: "POST", headers, body: JSON.stringify(body), signal: AbortSignal.timeout(CALL_TIMEOUT_MS) });
		if (!res.ok) throw new Error(`memory ${String(body.method)}: HTTP ${res.status}`);
		return res;
	};
	const init = await post({
		jsonrpc: "2.0",
		id: ++id,
		method: "initialize",
		params: { protocolVersion: "2025-03-26", capabilities: {}, clientInfo: { name: "mission-control-omp-hook", version: "1" } },
	});
	await init.text();
	const sid = init.headers.get("mcp-session-id");
	if (sid) headers["Mcp-Session-Id"] = sid;
	await (await post({ jsonrpc: "2.0", method: "notifications/initialized" })).text();
	return async (tool, args) => {
		const res = await post({ jsonrpc: "2.0", id: ++id, method: "tools/call", params: { name: tool, arguments: args } });
		const raw = await res.text();
		// The reply is one JSON-RPC message, either bare or as a single server-sent event.
		const data = raw.split("\n").find((l) => l.startsWith("data:"))?.slice(5) ?? raw;
		const msg = JSON.parse(data) as { error?: { message?: string }; result?: { isError?: boolean; content?: { text?: string }[] } };
		if (msg.error) throw new Error(`memory ${tool}: ${msg.error.message}`);
		const text = (msg.result?.content ?? []).map((c) => c.text ?? "").join("\n");
		if (msg.result?.isError) throw new Error(`memory ${tool}: ${text.slice(0, 300)}`);
		return text;
	};
}

/** Retains each spooled slice (a file is deleted only after every part of it was accepted), then recalls. Returns the context for the first run. */
async function warm(): Promise<string> {
	const files = queued();
	const notes: string[] = [];
	let call: Awaited<ReturnType<typeof connect>>;
	try {
		call = await connect();
	} catch (e) {
		return `Memory could not be reached at start (${(e as Error).message}). Tell the person once that memory is unavailable this session, and carry on.`;
	}
	for (const file of files) {
		try {
			const text = readFileSync(file, "utf8");
			const at = statSync(file).mtime.toISOString();
			for (let i = 0; i < text.length; i += CHUNK) {
				await call("memory_retain", { text: `Conversation slice from a previous session (${at}):\n\n${text.slice(i, i + CHUNK)}`, mention_time: at });
			}
			unlinkSync(file);
		} catch (e) {
			notes.push(`Retaining ${file} failed (${(e as Error).message}); it stays queued for the next start.`);
		}
	}
	try {
		const recalled = await call("memory_recall", { query: RECALL_QUERY });
		return `Memory recalled at session start (already done; do not call memory_recall again for this):\n${recalled}${notes.length ? "\n" + notes.join("\n") : ""}`;
	} catch (e) {
		return `Memory recall failed at start (${(e as Error).message}). Tell the person once, and carry on.${notes.length ? "\n" + notes.join("\n") : ""}`;
	}
}

type Entry = {
	type?: string;
	customType?: string;
	message?: { role?: string; content?: unknown };
};

function textOf(content: unknown): string {
	if (typeof content === "string") return content;
	if (!Array.isArray(content)) return "";
	return content
		.filter((b): b is { type?: string; text?: string } => !!b && typeof b === "object")
		.filter((b) => b.type === "text")
		.map((b) => b.text ?? "")
		.join("\n");
}

/** The user/assistant text of a session, with the criteria the other clients use: a real conversation, not a one-line exchange. */
function slice(entries: readonly Entry[]): string {
	const lines: string[] = [];
	let users = 0;
	for (const entry of entries) {
		if (entry.type !== "message" || entry.customType) continue;
		const role = entry.message?.role;
		if (role !== "user" && role !== "assistant") continue;
		const text = textOf(entry.message?.content).trim();
		if (!text || text.startsWith("<hippocampus-memory>")) continue;
		if (role === "user") users++;
		lines.push(`${role}: ${text}`);
	}
	const text = lines.join("\n\n");
	if (users < 4 && text.length < 4000) return "";
	return text.slice(-CAP);
}

function spool(file: string | null, entries: readonly Entry[]): void {
	if (!file) return;
	const text = slice(entries);
	if (!text) return;
	const dir = queueDir();
	mkdirSync(dir, { recursive: true, mode: 0o700 });
	const name = (file.split("/").pop() || "session").replace(/\.jsonl$/, "").replace(/[^A-Za-z0-9_-]/g, "_") + ".txt";
	writeFileSync(join(dir, name), text, { mode: 0o600 });
	const kept = readdirSync(dir)
		.filter((f) => f.endsWith(".txt"))
		.map((f) => ({ f, at: statSync(join(dir, f)).mtimeMs }))
		.sort((a, b) => b.at - a.at);
	for (const { f } of kept.slice(MAX_SPOOLED)) unlinkSync(join(dir, f));
}

export default function (pi: HookAPI): void {
	if (DISABLED) return;
	let ready: Promise<string> | undefined;
	let injected = false;
	// At process start, before any message: the memory work runs now, not on the first turn.
	pi.on("session_start", () => {
		ready ??= warm().catch((e) => `Memory start-up failed (${(e as Error).message}). Tell the person once, and carry on.`);
	});
	pi.on("before_agent_start", async () => {
		if (injected) return; // once per process; a resumed session is a new process
		injected = true;
		ready ??= warm().catch((e) => `Memory start-up failed (${(e as Error).message}). Tell the person once, and carry on.`);
		const context = await Promise.race([
			ready,
			new Promise<string>((r) => setTimeout(() => r("Memory is still loading at the first message. Tell the person once that memory was not ready, and carry on."), FIRST_RUN_WAIT_MS)),
		]);
		return { message: { customType: "mission-control-memory", content: `<hippocampus-memory>\n${context}\n</hippocampus-memory>`, display: false } };
	});
	pi.on("session_shutdown", (_event, ctx) => {
		try {
			spool(ctx.sessionManager.getSessionFile(), ctx.sessionManager.getEntries() as Entry[]);
		} catch {
			// fail-open: memory is never worth breaking a session end
		}
	});
}
