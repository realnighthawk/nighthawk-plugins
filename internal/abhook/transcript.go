package abhook

import (
	"bufio"
	"encoding/json"
	"io"
	"os"
	"regexp"
	"strings"
)

// Turn is one thing worth remembering from a session: what the user asked, what the assistant said, or a
// one-line action naming a tool call and its target.
type Turn struct {
	Role, Content, Timestamp string
}

const maxTurnChars = 1500

var memoryBlock = regexp.MustCompile(`(?s)<agent-brain-memory>.*?</agent-brain-memory>`)

var targetKeys = []string{"file_path", "path", "notebook_path", "pattern", "url", "query", "command", "description"}

func stripMemory(s string) string { return strings.TrimSpace(memoryBlock.ReplaceAllString(s, "")) }

// clip keeps the start and end of a long turn.
func clip(s string) string {
	r := []rune(s)
	if len(r) <= maxTurnChars {
		return s
	}
	return string(r[:maxTurnChars*2/3]) + " ... " + string(r[len(r)-maxTurnChars/3:])
}

func actionLine(name string, input any) string {
	target := ""
	if m, ok := input.(map[string]any); ok {
		for _, key := range targetKeys {
			if v, ok := m[key].(string); ok && strings.TrimSpace(v) != "" {
				target = truncate(strings.Join(strings.Fields(v), " "), 100)
				break
			}
		}
	}
	return strings.TrimSpace(name + " " + target)
}

type transcriptLine struct {
	Type, Timestamp                       string
	IsMeta, IsSidechain, IsCompactSummary bool
	Message                               *struct{ Content json.RawMessage }
}

// ReadClaudeTranscript parses a Claude Code session transcript (JSONL). It keeps user and assistant text
// and one line per tool call. It drops thinking blocks, tool results, meta and sidechain (subagent) lines,
// Claude Code's own compaction summaries, and any recalled-memory block this plugin injected, so memory is
// never written back as something the user said.
func ReadClaudeTranscript(path string) []Turn {
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()
	var turns []Turn
	r := bufio.NewReaderSize(f, 1<<20)
	for {
		raw, err := r.ReadBytes('\n')
		if len(raw) > 0 {
			turns = append(turns, renderLine(raw)...)
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			break
		}
	}
	return turns
}

func renderLine(raw []byte) []Turn {
	var line transcriptLine
	if json.Unmarshal(raw, &line) != nil || (line.Type != "user" && line.Type != "assistant") {
		return nil
	}
	if line.IsMeta || line.IsSidechain || line.IsCompactSummary || line.Message == nil {
		return nil
	}
	var out []Turn
	add := func(role, content string) {
		if content != "" {
			out = append(out, Turn{Role: role, Content: content, Timestamp: line.Timestamp})
		}
	}
	var text string
	if json.Unmarshal(line.Message.Content, &text) == nil {
		add(line.Type, clip(stripMemory(text)))
		return out
	}
	var blocks []map[string]any
	if json.Unmarshal(line.Message.Content, &blocks) != nil {
		return nil
	}
	var texts []string
	var actions []string
	for _, b := range blocks {
		switch b["type"] {
		case "text":
			if s, ok := b["text"].(string); ok {
				if s = stripMemory(s); s != "" {
					texts = append(texts, s)
				}
			}
		case "tool_use":
			if name, ok := b["name"].(string); ok {
				actions = append(actions, actionLine(name, b["input"]))
			}
		}
	}
	if joined := strings.TrimSpace(strings.Join(texts, "\n")); joined != "" {
		add(line.Type, clip(joined))
	}
	for _, a := range actions {
		add("action", a)
	}
	return out
}
