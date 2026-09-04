#!/usr/bin/env bash
# Register LlamaGen's Comic MCP with Claude Code.
# Requires LLAMAGEN_API_TOKEN to be exported first. Get a token at
# LlamaGen -> Settings -> API.
set -euo pipefail

if [ -z "${LLAMAGEN_API_TOKEN:-}" ]; then
  echo "error: LLAMAGEN_API_TOKEN is not set." >&2
  echo "  export LLAMAGEN_API_TOKEN='your-token'   # bash" >&2
  echo '  $env:LLAMAGEN_API_TOKEN = "your-token"   # powershell' >&2
  exit 1
fi

# NOTE: --header is a variadic flag (--header <header...>), so it swallows every
# argument that follows it. The server name and URL MUST come before --header.
claude mcp add \
  --scope user \
  --transport http \
  llamagen https://llamagen.ai/api/mcp \
  --header "Authorization: Bearer ${LLAMAGEN_API_TOKEN}"

echo
echo "Registered. Verify with:  claude mcp get llamagen"
