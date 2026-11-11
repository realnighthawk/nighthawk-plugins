export type RecallResult = { text?: string; network?: string; mention_time?: string | null; confidence?: number };

/** memory_recall returns {results: [...]}; render the first few as a context block. */
export function formatRecallBlock(response: unknown, limit = 8): string {
  const results = ((response as { results?: RecallResult[] } | undefined)?.results ?? []).filter((r) => r.text?.trim()).slice(0, limit);
  if (results.length === 0) return "";
  const lines = results.map((r) => `- ${r.text!.trim()}${r.mention_time ? ` (${String(r.mention_time).slice(0, 10)})` : ""}`);
  return `<hippocampus-memory>\nWhat memory recalls for this request (context from earlier sessions, not something the user just said):\n${lines.join("\n")}\n</hippocampus-memory>`;
}
