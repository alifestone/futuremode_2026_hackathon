# LUNA — LIVE AI Comic

An editable comic project for CSFCCA's virtual idol **LUNA**, derived from
`LUNA_MV_製作計畫書.docx` and the existing character sheet.

Claude Code owns the files and automation; LlamaGen's Comic MCP does the visual
generation and refinement.

## Layout

```
luna-comic/
├── project.json              # character bible, style lock, generation settings
├── panels/panels.json        # THE EDITABLE SOURCE — 13 panels across 4 pages
├── assets/reference/         # LUNA character sheet (consistency anchor)
├── scripts/
│   ├── connect_mcp.sh        # one-time MCP registration
│   └── build_prompts.py      # panels.json -> out/prompts.json
└── out/prompts.json          # compiled prompts + change hashes (generated)
```

## Setup

1. Get an API token from LlamaGen → Settings → API.
2. Export it, then register the MCP:

   ```bash
   export LLAMAGEN_API_TOKEN='your-token'
   bash scripts/connect_mcp.sh
   ```

   PowerShell equivalent — keep it on **one line**:

   ```powershell
   $env:LLAMAGEN_API_TOKEN = "your-token"
   claude mcp add --scope user --transport http llamagen https://llamagen.ai/api/mcp --header "Authorization: Bearer $env:LLAMAGEN_API_TOKEN"
   ```

   > `--header` is variadic (`--header <header...>`), so it consumes everything
   > after it. The name and URL must come **before** `--header`, or the CLI
   > fails with `error: missing required argument 'name'`.

3. Restart Claude Code, confirm with `/mcp` or `claude mcp get llamagen`.

## The edit loop

The point of this structure: **panels.json is the only file you edit by hand.**

1. Edit a panel's `action`, `expression`, `camera`, or `caption`.
2. `python scripts/build_prompts.py` — reports exactly which panels changed.
3. Ask Claude Code to regenerate only the changed panels via the LlamaGen MCP.

Because every panel carries the same `character_ref` and the same
`locked_keywords` from `project.json`, regenerating one panel does not drift the
others — the consistency problem the plan doc calls out as the project's main risk.

## Generation rules

Per LlamaGen's integration guide, before any generation:

- Call `get_comic_api_usage` first.
- **Stop if remaining credits < 5,000.**
- Get explicit approval before starting a batch — LlamaGen credits are separate
  from Claude Code usage costs.

Available MCP tools: `search_llamagen_docs`, `get_comic_api_usage`,
`create_comic_generation`, `get_comic_generation_status`.

## Source material

| Asset | Role |
|---|---|
| `動畫_女生_LUNA.jpg` | Character sheet: 4 angles, 9 expressions, 5 traits |
| `《CSFCCA LIVE AI》_ALL_NEW.mp3` | Track, ~2:14 — panel timings map to it |
| `LUNA_MV_製作計畫書.docx` | Production plan, storyboard strategy, prompt structure |
