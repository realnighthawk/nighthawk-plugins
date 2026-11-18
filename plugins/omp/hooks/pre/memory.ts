/**
 * Mission Control memory hooks for oh-my-pi.
 *
 * Signal-only, like the other clients: no network call, no credential. Before the process's first agent run the hook injects a
 * <hippocampus-memory> instruction: recall through the agent's own MCP connection, and retain any slice the previous session spooled. At
 * shutdown it writes a compact slice of the session to the retain queue so the next session can retain it. Fail-open: a hook never breaks a turn.
 */
import type { HookAPI } from "@oh-my-pi/pi-coding-agent/extensibility/hooks";
import { mkdirSync, readdirSync, statSync, unlinkSync, writeFileSync } from "node:fs";
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

function instruction(): string {
	let files: string[] = [];
	try {
		files = readdirSync(queueDir())
			.filter((f) => f.endsWith(".txt"))
			.slice(0, 5)
			.map((f) => join(queueDir(), f));
	} catch {
		// no queue yet
	}
	let text =
		"<hippocampus-memory>\nHippocampus memory is connected. Before answering the first request:\n" +
		" 1. call memory_recall on the Hippocampus MCP with a short query about this project and the user; if the tool is unavailable or needs authentication, say so once and continue.";
	if (files.length) {
		text +=
			"\n 2. Retain the deferred session slices below first: read each file below and call memory_retain with a short, dated account of it, then delete the file.\nDeferred:\n" +
			files.map((f) => "  - " + f).join("\n");
	}
	return text + "\n</hippocampus-memory>";
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
	let injected = false;
	pi.on("before_agent_start", () => {
		if (injected) return; // once per process; a resumed session is a new process
		injected = true;
		return { message: { customType: "mission-control-memory", content: instruction(), display: false } };
	});
	pi.on("session_shutdown", (_event, ctx) => {
		try {
			spool(ctx.sessionManager.getSessionFile(), ctx.sessionManager.getEntries() as Entry[]);
		} catch {
			// fail-open: memory is never worth breaking a session end
		}
	});
}
