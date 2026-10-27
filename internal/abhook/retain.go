package abhook

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
	"unicode"
)

const maxPayloadChars = 12000

type outboxItem struct {
	BankID      string `json:"bank_id"`
	Text        string `json:"text"`
	MentionTime string `json:"mention_time"`
}

func safeName(s string) string {
	if s == "" {
		return "no-session"
	}
	out := []rune{}
	for _, r := range s {
		if unicode.IsLetter(r) || unicode.IsDigit(r) || r == '-' || r == '_' {
			out = append(out, r)
		} else {
			out = append(out, '_')
		}
	}
	return truncate(string(out), 80)
}

func renderTurn(t Turn) string { return t.Role + ": " + t.Content }

// payloads cuts turns into chunks of at most maxPayloadChars at turn boundaries and renders each as the
// text memory_retain takes, with the time of its last turn.
func payloads(project string, turns []Turn) (out []outboxItem, covered []int) {
	var chunk []Turn
	size := 0
	flush := func() {
		if len(chunk) == 0 {
			return
		}
		stamp := ""
		for i := len(chunk) - 1; i >= 0 && stamp == ""; i-- {
			stamp = chunk[i].Timestamp
		}
		if stamp == "" {
			stamp = time.Now().UTC().Format(time.RFC3339)
		}
		lines := make([]string, len(chunk))
		for i, t := range chunk {
			lines[i] = renderTurn(t)
		}
		header := fmt.Sprintf("A Claude Code session in the project %s, between the user and the assistant:", project)
		out = append(out, outboxItem{Text: header + "\n" + strings.Join(lines, "\n"), MentionTime: stamp})
		covered = append(covered, len(chunk))
		chunk, size = nil, 0
	}
	for _, t := range turns {
		n := len([]rune(renderTurn(t))) + 1
		if len(chunk) > 0 && size+n > maxPayloadChars {
			flush()
		}
		chunk = append(chunk, t)
		size += n
	}
	flush()
	return out, covered
}

// Queue writes the turns added since the last call into the outbox. In stop mode it waits until enough
// have built up (MinTurns turns or MinChars characters); in flush mode it queues whatever is new. It
// returns the number of payloads queued.
func Queue(c Config, e Event, turns []Turn, flush bool) (int, error) {
	session := safeName(e.SessionID)
	cursorDir := filepath.Join(c.StateDir, "cursors")
	outbox := filepath.Join(c.StateDir, "outbox")
	if err := os.MkdirAll(cursorDir, 0o755); err != nil {
		return 0, err
	}
	cursorFile := filepath.Join(cursorDir, session+".json")
	var cur struct{ Queued int }
	if data, err := os.ReadFile(cursorFile); err == nil {
		_ = json.Unmarshal(data, &cur)
	}
	if cur.Queued > len(turns) {
		cur.Queued = len(turns)
	}
	delta := turns[cur.Queued:]
	chars, hasUser := 0, false
	for _, t := range delta {
		chars += len([]rune(renderTurn(t)))
		hasUser = hasUser || t.Role == "user"
	}
	if len(delta) == 0 || !hasUser || chars < 200 {
		return 0, nil
	}
	if !flush && len(delta) < c.MinTurns && chars < c.MinChars {
		return 0, nil
	}
	cwd := e.CWD
	if cwd == "" {
		cwd, _ = os.Getwd()
	}
	items, counts := payloads(filepath.Base(cwd), delta)
	if err := os.MkdirAll(outbox, 0o755); err != nil {
		return 0, err
	}
	covered := cur.Queued
	for i, item := range items {
		item.BankID = c.Bank
		data, _ := json.Marshal(item)
		name := filepath.Join(outbox, fmt.Sprintf("%020d-%s-%d.json", time.Now().UnixNano(), session, i))
		if err := os.WriteFile(name, data, 0o644); err != nil {
			return i, err
		}
		covered += counts[i]
		data, _ = json.Marshal(struct{ Queued int }{covered})
		if err := os.WriteFile(cursorFile, data, 0o644); err != nil {
			return i + 1, err
		}
	}
	return len(items), nil
}

// HasOutbox reports whether any payload is waiting to be sent.
func HasOutbox(c Config) bool {
	files, _ := filepath.Glob(filepath.Join(c.StateDir, "outbox", "*.json"))
	return len(files) > 0
}

// Drain sends queued payloads to memory_retain in order. A payload that fails stays queued, and draining
// stops there so order is kept; the next hook retries it.
func Drain(ctx context.Context, c Config) int {
	files, _ := filepath.Glob(filepath.Join(c.StateDir, "outbox", "*.json"))
	sort.Strings(files)
	sent := 0
	for _, f := range files {
		data, err := os.ReadFile(f)
		if err != nil {
			continue
		}
		var item outboxItem
		if json.Unmarshal(data, &item) != nil {
			_ = os.Rename(f, f+".bad")
			continue
		}
		cctx, cancel := context.WithTimeout(ctx, c.RetainTimeout)
		_, err = c.CallTool(cctx, "memory_retain", map[string]any{
			"bank_id": item.BankID, "text": item.Text, "mention_time": item.MentionTime,
		})
		cancel()
		if err != nil {
			c.Logf("retain failed, will retry: %v", err)
			break
		}
		_ = os.Remove(f)
		sent++
	}
	return sent
}
