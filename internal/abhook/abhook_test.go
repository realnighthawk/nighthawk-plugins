package abhook

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type call struct {
	tool string
	args map[string]any
}

type mock struct {
	mu         sync.Mutex
	calls      []call
	failRetain bool
	srv        *httptest.Server
}

func newMock(t *testing.T) *mock {
	m := &mock{}
	s := server.NewMCPServer("mock", "1")
	record := func(tool string, text func() string) server.ToolHandlerFunc {
		return func(_ context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			m.mu.Lock()
			defer m.mu.Unlock()
			m.calls = append(m.calls, call{tool, req.GetArguments()})
			if tool == "memory_retain" && m.failRetain {
				return mcp.NewToolResultError("boom"), nil
			}
			return mcp.NewToolResultText(text()), nil
		}
	}
	s.AddTool(mcp.NewTool("memory_recall", mcp.WithString("bank_id"), mcp.WithString("query")),
		record("memory_recall", func() string {
			return `{"results":[{"memory_unit_id":"u1","text":"Dana prefers tabs.","network":"world"}]}`
		}))
	s.AddTool(mcp.NewTool("memory_retain", mcp.WithString("bank_id"), mcp.WithString("text"), mcp.WithString("mention_time")),
		record("memory_retain", func() string { return `{"status":"ok"}` }))
	m.srv = server.NewTestStreamableHTTPServer(s)
	t.Cleanup(m.srv.Close)
	return m
}

func (m *mock) retains() []call {
	m.mu.Lock()
	defer m.mu.Unlock()
	var out []call
	for _, c := range m.calls {
		if c.tool == "memory_retain" {
			out = append(out, c)
		}
	}
	return out
}

func testConfig(t *testing.T, m *mock) Config {
	return Config{URL: m.srv.URL, APIKey: "k", Bank: "me", RecallLimit: 8, RecallTimeout: 5e9, RetainTimeout: 10e9,
		MinTurns: 6, MinChars: 4000, StateDir: t.TempDir()}
}

func jl(kind string, content any, extra map[string]any) string {
	line := map[string]any{"type": kind, "timestamp": "2026-10-26T10:00:00Z", "message": map[string]any{"role": kind, "content": content}}
	for k, v := range extra {
		line[k] = v
	}
	b, _ := json.Marshal(line)
	return string(b)
}

func writeTranscript(t *testing.T, lines ...string) string {
	p := filepath.Join(t.TempDir(), "t.jsonl")
	require.NoError(t, os.WriteFile(p, []byte(strings.Join(lines, "\n")+"\n"), 0o644))
	return p
}

func TestTranscriptKeepsSubstanceAndDropsNoise(t *testing.T) {
	p := writeTranscript(t,
		jl("user", "Please fix the parser bug <agent-brain-memory>\n- secret recalled fact\n</agent-brain-memory>", nil),
		jl("assistant", []any{
			map[string]any{"type": "thinking", "thinking": "hmm"},
			map[string]any{"type": "text", "text": "Looking at it."},
			map[string]any{"type": "tool_use", "name": "Edit", "input": map[string]any{"file_path": "src/parser.py", "old_string": "x"}},
		}, nil),
		jl("user", []any{map[string]any{"type": "tool_result", "content": "huge output"}}, nil),
		jl("user", "meta line", map[string]any{"isMeta": true}),
		jl("user", "compact recap", map[string]any{"isCompactSummary": true}),
		jl("assistant", "side chain", map[string]any{"isSidechain": true}),
		"not json", `{"type":"summary","summary":"x"}`, "null",
	)
	var got []string
	for _, turn := range ReadClaudeTranscript(p) {
		got = append(got, turn.Role+"|"+turn.Content)
	}
	assert.Equal(t, []string{"user|Please fix the parser bug", "assistant|Looking at it.", "action|Edit src/parser.py"}, got)
}

func TestRecallInjectsTaggedBlockAndSendsKey(t *testing.T) {
	m := newMock(t)
	cfg := testConfig(t, m)
	out := Recall(context.Background(), cfg, Event{Prompt: "What indentation does Dana prefer in this repo?"})
	var parsed struct {
		H struct{ AdditionalContext string } `json:"hookSpecificOutput"`
	}
	require.NoError(t, json.Unmarshal([]byte(out), &parsed))
	assert.Contains(t, parsed.H.AdditionalContext, "<agent-brain-memory>")
	assert.Contains(t, parsed.H.AdditionalContext, "Dana prefers tabs.")
	require.Len(t, m.calls, 1)
	assert.Equal(t, "memory_recall", m.calls[0].tool)
	assert.Equal(t, "me", m.calls[0].args["bank_id"])
}

func TestRecallIsSilentWhenUnconfiguredShortOrServerDown(t *testing.T) {
	m := newMock(t)
	cfg := testConfig(t, m)
	empty := ContextOutput("UserPromptSubmit", "")
	bare := cfg
	bare.URL = ""
	assert.Equal(t, empty, Recall(context.Background(), bare, Event{Prompt: "long enough prompt here"}))
	assert.Equal(t, empty, Recall(context.Background(), cfg, Event{Prompt: "short"}))
	assert.Equal(t, empty, Recall(context.Background(), cfg, Event{Prompt: "/clear everything please now"}))
	assert.Empty(t, m.calls)
	down := cfg
	down.URL = "http://127.0.0.1:9/mcp"
	assert.Equal(t, empty, Recall(context.Background(), down, Event{Prompt: "a prompt while the server is down"}))
}

func session(lines int) []string {
	out := []string{
		jl("user", "Use tabs for indentation in this project, always, including in generated files and in the docs examples.", nil),
		jl("assistant", "Understood, switching the formatter configuration to tabs everywhere in the repository right now.", nil),
	}
	for i := 0; i < lines; i++ {
		if i%2 == 0 {
			out = append(out, jl("user", fmt.Sprintf("step %d of the migration plan we agreed on", i), nil))
		} else {
			out = append(out, jl("assistant", fmt.Sprintf("done with step %d of the plan", i), nil))
		}
	}
	return out
}

func TestRetainWaitsForThresholdThenSendsOnlyNewTurns(t *testing.T) {
	m := newMock(t)
	cfg := testConfig(t, m)
	ctx := context.Background()
	ev := func(p string) Event { return Event{SessionID: "s1", TranscriptPath: p, CWD: "/work/acme"} }

	p := writeTranscript(t, session(0)...)
	n, err := Queue(cfg, ev(p), ReadClaudeTranscript(p), false)
	require.NoError(t, err)
	assert.Zero(t, n, "two turns are below the threshold")

	p = writeTranscript(t, session(6)...)
	n, err = Queue(cfg, ev(p), ReadClaudeTranscript(p), false)
	require.NoError(t, err)
	assert.Equal(t, 1, n)
	assert.Equal(t, 1, Drain(ctx, cfg))
	sent := m.retains()
	require.Len(t, sent, 1)
	assert.Equal(t, "me", sent[0].args["bank_id"])
	assert.Equal(t, "2026-10-26T10:00:00Z", sent[0].args["mention_time"])
	assert.Contains(t, sent[0].args["text"], "project acme")
	assert.Contains(t, sent[0].args["text"], "user: Use tabs for indentation")

	n, _ = Queue(cfg, ev(p), ReadClaudeTranscript(p), false)
	assert.Zero(t, n, "the same turns are not queued twice")

	more := append(session(6),
		jl("user", "Also remember that Dana owns the release process, including cutting tags and writing the changelog every Friday.", nil),
		jl("assistant", "Noted: Dana owns the release process, including cutting tags and writing the changelog every Friday afternoon.", nil))
	p = writeTranscript(t, more...)
	n, err = Queue(cfg, ev(p), ReadClaudeTranscript(p), true)
	require.NoError(t, err)
	assert.Equal(t, 1, n)
	Drain(ctx, cfg)
	sent = m.retains()
	require.Len(t, sent, 2)
	assert.NotContains(t, sent[1].args["text"], "Use tabs", "flush sends only what is new")
	assert.Contains(t, sent[1].args["text"], "Dana owns the release process")
}

func TestFailedRetainStaysQueuedAndIsRetried(t *testing.T) {
	m := newMock(t)
	cfg := testConfig(t, m)
	p := writeTranscript(t, session(0)...)
	_, err := Queue(cfg, Event{SessionID: "s2", TranscriptPath: p, CWD: "/work/acme"}, ReadClaudeTranscript(p), true)
	require.NoError(t, err)
	m.failRetain = true
	assert.Zero(t, Drain(context.Background(), cfg))
	assert.True(t, HasOutbox(cfg), "kept for retry")
	m.failRetain = false
	assert.Equal(t, 1, Drain(context.Background(), cfg))
	assert.False(t, HasOutbox(cfg))
	assert.Len(t, m.retains(), 2)
}

func TestLongSessionIsSplitIntoBoundedPayloads(t *testing.T) {
	var turns []Turn
	for i := 0; i < 40; i++ {
		role := "user"
		if i%2 == 1 {
			role = "assistant"
		}
		turns = append(turns, Turn{Role: role, Content: strings.Repeat("word ", 300)})
	}
	items, counts := payloads("acme", turns)
	total := 0
	for i, it := range items {
		assert.LessOrEqual(t, len([]rune(it.Text)), maxPayloadChars+200)
		total += counts[i]
	}
	assert.Greater(t, len(items), 1)
	assert.Equal(t, 40, total, "every turn lands in exactly one payload")
}

func TestConfigFileIsOverriddenByEnvironment(t *testing.T) {
	dir := t.TempDir()
	file := filepath.Join(dir, "plugin.env")
	require.NoError(t, os.WriteFile(file, []byte("# comment\nAGENT_BRAIN_MCP_URL=http://file/mcp\nAGENT_BRAIN_BANK=\"filebank\"\n"), 0o644))
	t.Setenv("AGENT_BRAIN_CONFIG", file)
	t.Setenv("AGENT_BRAIN_BANK", "envbank")
	cfg := LoadConfig()
	assert.Equal(t, "http://file/mcp", cfg.URL)
	assert.Equal(t, "envbank", cfg.Bank)
	assert.False(t, cfg.Disabled())
	t.Setenv("AGENT_BRAIN_DISABLE_HOOKS", "1")
	assert.True(t, LoadConfig().Disabled())
}
