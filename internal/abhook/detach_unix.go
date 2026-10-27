//go:build !windows

package abhook

import (
	"os"
	"os/exec"
	"syscall"
)

// SpawnDrain starts `agent-brain-hook retain drain` in its own session so it outlives the hook.
func SpawnDrain() error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	cmd := exec.Command(exe, "retain", "drain")
	cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true}
	cmd.Env = os.Environ()
	if err := cmd.Start(); err != nil {
		return err
	}
	return cmd.Process.Release()
}
