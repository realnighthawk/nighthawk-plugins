// agent-brain-hook is the hook command for coding-agent plugins (Claude Code first).
//
//	agent-brain-hook recall            UserPromptSubmit: inject facts relevant to the prompt
//	agent-brain-hook session-start     SessionStart: inject facts about the project
//	agent-brain-hook retain stop       Stop: queue new turns once enough have built up
//	agent-brain-hook retain flush      PreCompact, SessionEnd: queue whatever is new
//	agent-brain-hook retain drain      (internal) send queued payloads to memory_retain
//
// Settings come from AGENT_BRAIN_* environment variables or ~/.config/agent-brain/plugin.env.
// Every command exits 0: a hook must never fail the agent's prompt.
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/realnighthawk/agent-plugins/internal/abhook"
)

func main() {
	defer func() {
		if r := recover(); r != nil {
			abhook.LoadConfig().Logf("panic: %v", r)
		}
	}()
	if len(os.Args) < 2 {
		return
	}
	cfg := abhook.LoadConfig()
	ctx := context.Background()
	switch os.Args[1] {
	case "recall":
		fmt.Println(abhook.Recall(ctx, cfg, abhook.ReadEvent(os.Stdin)))
	case "session-start":
		fmt.Println(abhook.SessionStart(ctx, cfg, abhook.ReadEvent(os.Stdin)))
	case "retain":
		retain(ctx, cfg)
	}
}

func retain(ctx context.Context, cfg abhook.Config) {
	if cfg.Disabled() || len(os.Args) < 3 {
		return
	}
	mode := os.Args[2]
	if mode == "drain" {
		abhook.Drain(ctx, cfg)
		return
	}
	e := abhook.ReadEvent(os.Stdin)
	turns := abhook.ReadClaudeTranscript(e.TranscriptPath)
	if _, err := abhook.Queue(cfg, e, turns, mode == "flush"); err != nil {
		cfg.Logf("queue failed: %v", err)
		return
	}
	if !abhook.HasOutbox(cfg) {
		return
	}
	if os.Getenv("AGENT_BRAIN_SYNC") != "" { // tests and debugging
		abhook.Drain(ctx, cfg)
		return
	}
	if err := abhook.SpawnDrain(); err != nil {
		cfg.Logf("spawn drain failed: %v", err)
	}
}
