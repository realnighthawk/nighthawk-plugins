package abhook

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// Event is the JSON a coding agent passes a hook on stdin; only the fields the hooks use.
type Event struct {
	SessionID      string `json:"session_id"`
	TranscriptPath string `json:"transcript_path"`
	CWD            string `json:"cwd"`
	Prompt         string `json:"prompt"`
}

// ReadEvent parses the hook event from r; malformed input yields an empty event.
func ReadEvent(r io.Reader) Event {
	var e Event
	data, _ := io.ReadAll(r)
	_ = json.Unmarshal(data, &e)
	return e
}

const memoryOpen, memoryClose = "<agent-brain-memory>", "</agent-brain-memory>"

// MemoryBlock formats recalled facts as one tagged block; the tags let the retain hook strip it from the
// transcript. It returns "" when there is nothing to inject.
func MemoryBlock(results []any, limit int) string {
	var lines []string
	for _, item := range results {
		if m, ok := item.(map[string]any); ok {
			if text, ok := m["text"].(string); ok && strings.TrimSpace(text) != "" {
				lines = append(lines, "- "+strings.TrimSpace(text))
			}
		}
		if len(lines) == limit {
			break
		}
	}
	if len(lines) == 0 {
		return ""
	}
	return memoryOpen + "\nWhat long-term memory holds that may bear on this:\n" + strings.Join(lines, "\n") + "\n" + memoryClose
}

// ContextOutput is the hook response that injects additional context into the agent.
func ContextOutput(eventName, block string) string {
	inner := map[string]any{"hookEventName": eventName}
	if block != "" {
		inner["additionalContext"] = block
	}
	out, _ := json.Marshal(map[string]any{"hookSpecificOutput": inner})
	return string(out)
}

func (c Config) recallBlock(ctx context.Context, query string) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, c.RecallTimeout)
	defer cancel()
	res, err := c.CallTool(ctx, "memory_recall", map[string]any{"bank_id": c.Bank, "query": query})
	if err != nil {
		return "", err
	}
	results, _ := res["results"].([]any)
	return MemoryBlock(results, c.RecallLimit), nil
}

// Recall is the UserPromptSubmit hook: facts relevant to the prompt.
func Recall(ctx context.Context, c Config, e Event) string {
	prompt := strings.Join(strings.Fields(e.Prompt), " ")
	if c.Disabled() || len([]rune(prompt)) < 12 || strings.HasPrefix(prompt, "/") {
		return ContextOutput("UserPromptSubmit", "")
	}
	block, err := c.recallBlock(ctx, truncate(prompt, 500))
	if err != nil {
		c.Logf("recall failed: %v", err)
		return ContextOutput("UserPromptSubmit", "")
	}
	return ContextOutput("UserPromptSubmit", block)
}

// SessionStart is the SessionStart hook: facts about the project.
func SessionStart(ctx context.Context, c Config, e Event) string {
	if c.Disabled() {
		return ContextOutput("SessionStart", "")
	}
	cwd := e.CWD
	if cwd == "" {
		cwd, _ = os.Getwd()
	}
	block, err := c.recallBlock(ctx, fmt.Sprintf("%s project decisions and user preferences", filepath.Base(cwd)))
	if err != nil {
		c.Logf("session start recall failed: %v", err)
		return ContextOutput("SessionStart", "")
	}
	return ContextOutput("SessionStart", block)
}
