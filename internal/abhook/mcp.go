package abhook

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	mcpclient "github.com/mark3labs/mcp-go/client"
	"github.com/mark3labs/mcp-go/client/transport"
	"github.com/mark3labs/mcp-go/mcp"
)

func sprintf(format string, args ...any) string { return fmt.Sprintf(format, args...) }

// CallTool opens a session to the memory server, calls one tool, and returns its JSON result.
// A tool that reports an error, and a result that is not a JSON object, are both errors.
func (c Config) CallTool(ctx context.Context, tool string, args map[string]any) (map[string]any, error) {
	headers := map[string]string{}
	if c.APIKey != "" {
		headers["X-API-Key"] = c.APIKey
	}
	cl, err := mcpclient.NewStreamableHttpClient(c.URL, transport.WithHTTPHeaders(headers))
	if err != nil {
		return nil, err
	}
	defer cl.Close()
	if err := cl.Start(ctx); err != nil {
		return nil, err
	}
	init := mcp.InitializeRequest{}
	init.Params.ProtocolVersion = mcp.LATEST_PROTOCOL_VERSION
	init.Params.ClientInfo = mcp.Implementation{Name: "agent-brain-hook", Version: "0.2.0"}
	if _, err := cl.Initialize(ctx, init); err != nil {
		return nil, err
	}
	res, err := cl.CallTool(ctx, mcp.CallToolRequest{Params: mcp.CallToolParams{Name: tool, Arguments: args}})
	if err != nil {
		return nil, err
	}
	var text strings.Builder
	for _, block := range res.Content {
		if t, ok := block.(mcp.TextContent); ok {
			text.WriteString(t.Text)
		}
	}
	if res.IsError {
		return nil, fmt.Errorf("%s: %s", tool, truncate(text.String(), 300))
	}
	if m, ok := res.StructuredContent.(map[string]any); ok {
		return m, nil
	}
	out := map[string]any{}
	if err := json.Unmarshal([]byte(text.String()), &out); err != nil {
		return nil, fmt.Errorf("%s: reply is not a JSON object", tool)
	}
	return out, nil
}

func truncate(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}
