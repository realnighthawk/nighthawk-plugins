// Package abhook implements the agent-brain hooks shared by coding-agent plugins: recall before a
// prompt, and retain of finished parts of a session. Every entry point is fail-open: a hook must
// never fail or slow the host agent's prompt.
package abhook

import (
	"bufio"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// Config holds the plugin settings. Environment variables win over the optional file
// ~/.config/agent-brain/plugin.env (KEY=VALUE lines), so a shell profile can override it.
type Config struct {
	URL, APIKey, Bank string
	RecallLimit       int
	RecallTimeout     time.Duration
	RetainTimeout     time.Duration
	MinTurns          int
	MinChars          int
	StateDir          string
	Disable           bool
}

func fileValues(path string) map[string]string {
	values := map[string]string{}
	f, err := os.Open(path)
	if err != nil {
		return values
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if k, v, ok := strings.Cut(line, "="); ok {
			values[strings.TrimSpace(k)] = strings.Trim(strings.TrimSpace(v), `"'`)
		}
	}
	return values
}

// LoadConfig reads settings from the environment and the optional config file.
func LoadConfig() Config {
	home, _ := os.UserHomeDir()
	path := os.Getenv("AGENT_BRAIN_CONFIG")
	if path == "" {
		path = filepath.Join(home, ".config", "agent-brain", "plugin.env")
	}
	file := fileValues(path)
	get := func(key string) string {
		if v, ok := os.LookupEnv(key); ok {
			return v
		}
		return file[key]
	}
	num := func(key string, def int) int {
		if n, err := strconv.Atoi(get(key)); err == nil && n > 0 {
			return n
		}
		return def
	}
	state := get("AGENT_BRAIN_STATE_DIR")
	if state == "" {
		state = filepath.Join(home, ".cache", "agent-brain")
	}
	return Config{
		URL:           get("AGENT_BRAIN_MCP_URL"),
		APIKey:        get("AGENT_BRAIN_API_KEY"),
		Bank:          get("AGENT_BRAIN_BANK"),
		RecallLimit:   num("AGENT_BRAIN_RECALL_LIMIT", 8),
		RecallTimeout: time.Duration(num("AGENT_BRAIN_RECALL_TIMEOUT", 8)) * time.Second,
		RetainTimeout: time.Duration(num("AGENT_BRAIN_RETAIN_TIMEOUT", 180)) * time.Second,
		MinTurns:      num("AGENT_BRAIN_RETAIN_MIN_TURNS", 6),
		MinChars:      num("AGENT_BRAIN_RETAIN_MIN_CHARS", 4000),
		StateDir:      state,
		Disable:       get("AGENT_BRAIN_DISABLE_HOOKS") != "",
	}
}

// Disabled reports whether hooks must do nothing: switched off, or no server URL or bank set.
func (c Config) Disabled() bool { return c.Disable || c.URL == "" || c.Bank == "" }

// Logf appends one line to the hook log. It never fails.
func (c Config) Logf(format string, args ...any) {
	_ = os.MkdirAll(c.StateDir, 0o755)
	f, err := os.OpenFile(filepath.Join(c.StateDir, "hook.log"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	line := time.Now().Format("2006-01-02T15:04:05") + " " + sprintf(format, args...) + "\n"
	_, _ = f.WriteString(line)
}
