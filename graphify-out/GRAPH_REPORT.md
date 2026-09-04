# Graph Report - futuremode_2026_hackathon  (2026-09-04)

## Corpus Check
- Corpus is ~32,064 words - fits in a single context window. You may not need a graph.

## Summary
- 216 nodes · 353 edges · 12 communities (11 shown, 1 thin omitted)
- Extraction: 80% EXTRACTED · 19% INFERRED · 1% AMBIGUOUS · INFERRED: 67 edges (avg confidence: 0.87)
- Token cost: 337,674 input · 0 output

## Community Hubs (Navigation)
- Song Sections and Narrative Shots
- LUNA Character Design Sheet
- Project Architecture and Assets
- Chorus Shots and Model Assignment
- Comic Panels and Generation Defaults
- Beat Grid and Audio Measurement
- LlamaGen MCP Integration
- Audio Analysis Internals
- Hologram Doubt Sequence
- Prompt Compiler Internals
- Verse Narrative Comic Page
- MCP Registration Script

## God Nodes (most connected - your core abstractions)
1. `Kling 3.0 (model assignment)` - 15 edges
2. `Nine-Panel Expression Grid` - 13 edges
3. `LUNA Character Sheet (reference asset)` - 10 edges
4. `LUNA (virtual idol character)` - 10 edges
5. `S24 - Final Pose and CSFCCA Logo Flare` - 8 edges
6. `Character Consistency (top project risk)` - 7 edges
7. `LlamaGen Comic MCP` - 7 edges
8. `Per-Shot Multi-Model Assignment` - 7 edges
9. `LUNA Storyboard Shot List (shots.json)` - 7 edges
10. `Measured Beatmap (beatmap.json)` - 7 edges

## Surprising Connections (you probably didn't know these)
- `LUNA (virtual idol, root sheet)` --semantically_similar_to--> `LUNA (virtual idol character)`  [INFERRED] [semantically similar]
  動畫_女生_LUNA.jpg → luna-comic/assets/reference/luna_character_sheet.jpg
- `Costume Keyword Lock (purple ponytail, white crop top, chains)` --semantically_similar_to--> `locked_keywords (costume lock)`  [INFERRED] [semantically similar]
  luna-comic/storyboard/STORYBOARD.md → CLAUDE.md
- `The Edit Loop (panels.json is the only hand-edited file)` --semantically_similar_to--> `Edit the JSON, Not the Compiled Output`  [INFERRED] [semantically similar]
  luna-comic/README.md → CLAUDE.md
- `S01 - Closed Eyes in Darkness` --references--> `S01 — Closed-Eye Close-Up in Darkness`  [INFERRED]
  luna-comic/storyboard/shots.json → luna-comic/storyboard/STORYBOARD.md
- `LUNA Character Sheet (root-level 動畫_女生_LUNA)` --semantically_similar_to--> `LUNA Character Sheet (reference asset)`  [INFERRED] [semantically similar]
  動畫_女生_LUNA.jpg → luna-comic/assets/reference/luna_character_sheet.jpg

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Character Consistency Mechanism** — claude_character_ref, claude_locked_keywords, claude_nine_expressions, claude_hero_shot_reference_workflow, luna_comic_storyboard_storyboard_max_shot_length_9_1s, claude_character_sheet [EXTRACTED 1.00]
- **Audio-to-Storyboard Pipeline** — claude_csfcca_live_ai_track, claude_analyze_audio_py, claude_beatmap_json, claude_shots_json, luna_comic_storyboard_storyboard_md [EXTRACTED 1.00]
- **LlamaGen Generation Guardrail Flow** — claude_generation_guardrails, claude_get_comic_api_usage, claude_create_comic_generation, claude_get_comic_generation_status, claude_llamagen_comic_mcp [EXTRACTED 1.00]
- **Bass Dropout and Return Arc** — luna_comic_storyboard_beatmap_section_breakdown, luna_comic_storyboard_shots_s20, luna_comic_storyboard_shots_s21, luna_comic_storyboard_shots_s22, luna_comic_storyboard_beatmap_hard_cut_84_26, luna_comic_storyboard_beatmap_hard_cut_93_32 [INFERRED 0.85]
- **Hologram Identity Crisis Thread** — luna_comic_storyboard_shots_s08, luna_comic_storyboard_shots_s09, luna_comic_storyboard_shots_s10, luna_comic_storyboard_shots_s11, luna_comic_storyboard_shots_s20 [INFERRED 0.85]
- **Beat-Locked Shot Generation Pipeline** — luna_comic_storyboard_beatmap_analyze_audio_py, luna_comic_storyboard_beatmap_tempo_grid, luna_comic_storyboard_beatmap_bar_grid_60, luna_comic_storyboard_shots_bar_line_alignment, luna_comic_storyboard_shots_storyboard, luna_comic_storyboard_shots_defaults [INFERRED 0.85]
- **Cross-Panel Character Consistency Lock** — luna_comic_panels_panels_character_ref, luna_comic_project_locked_keywords, luna_comic_project_reference_sheet, luna_comic_panels_panels_negative, luna_comic_project_style [INFERRED 0.85]
- **Four-Page Narrative Arc Timed to the Track** — luna_comic_panels_panels_page_1, luna_comic_panels_panels_page_2, luna_comic_panels_panels_page_3, luna_comic_panels_panels_page_4, luna_comic_project_audio [INFERRED 0.85]
- **Panel Generation Pipeline and Credit Guard** — luna_comic_project_generation, luna_comic_project_credit_floor, luna_comic_panels_panels_status_lifecycle, luna_comic_panels_panels_defaults [INFERRED 0.75]
- **LUNA Costume and Silhouette Design System** — luna_comic_assets_reference_luna_character_sheet_purple_braided_ponytail, luna_comic_assets_reference_luna_character_sheet_white_zip_crop_top, luna_comic_assets_reference_luna_character_sheet_white_cargo_miniskirt, luna_comic_assets_reference_luna_character_sheet_silver_chain_accessories, luna_comic_assets_reference_luna_character_sheet_white_platform_sneakers, luna_comic_assets_reference_luna_character_sheet_purple_white_palette [EXTRACTED 1.00]
- **LUNA Turnaround Angle Set** — luna_comic_assets_reference_luna_character_sheet_full_body_turnaround, luna_comic_assets_reference_luna_character_sheet_three_quarter_view, luna_comic_assets_reference_luna_character_sheet_side_profile_view [EXTRACTED 1.00]
- **LUNA Nine-Emotion Range Reference** — luna_comic_assets_reference_luna_character_sheet_expression_calm, luna_comic_assets_reference_luna_character_sheet_expression_happy, luna_comic_assets_reference_luna_character_sheet_expression_playful_wink, luna_comic_assets_reference_luna_character_sheet_expression_surprised, luna_comic_assets_reference_luna_character_sheet_expression_shy, luna_comic_assets_reference_luna_character_sheet_expression_angry, luna_comic_assets_reference_luna_character_sheet_expression_aggrieved, luna_comic_assets_reference_luna_character_sheet_expression_thinking, luna_comic_assets_reference_luna_character_sheet_expression_confident_smile [EXTRACTED 1.00]

## Communities (12 total, 1 thin omitted)

### Community 0 - "Song Sections and Narrative Shots"
Cohesion: 0.11
Nodes (33): First Beat Offset 0.488s, Hard Cut 11.81s - Bass Entry, Hard Cut 84.26s - Breakdown Dropout, Hard Cut 93.32s - Final Chorus Re-entry, Section: Breakdown (bar 38), Section: Build / Pre-drop (bar 6), Section: Chorus 1 ext. (bar 26), Section: Final chorus (bar 42) (+25 more)

### Community 1 - "LUNA Character Design Sheet"
Cohesion: 0.09
Nodes (32): LUNA Character Sheet (root-level 動畫_女生_LUNA), LUNA Visual Design Specification (hair, costume, palette), Root Character Sheet as Consistency Anchor, LUNA Expression Reference Set (nine emotions), LUNA (virtual idol, root sheet), LUNA Pose and Angle Reference Set, LUNA Character Sheet (reference asset), Anime Cel-Shaded Illustration Style (+24 more)

### Community 2 - "Project Architecture and Assets"
Cohesion: 0.11
Nodes (31): scripts/analyze_audio.py, Bar-Grid Snapping of Shot Boundaries, storyboard/beatmap.json (measured beat grid), scripts/build_prompts.py, 12-Char Prompt Change Hash, Character Consistency (top project risk), character_ref field, LUNA Character Sheet (動畫_女生_LUNA.jpg) (+23 more)

### Community 3 - "Chorus Shots and Model Assignment"
Cohesion: 0.10
Nodes (28): Six Hard Cut Points, Per-Shot Multi-Model Assignment, Phase One Teaser (S12 to S15), Hard Cut 45.77s - Chorus 1 Downbeat, Section: Chorus 1 (bar 21), Runway Gen-4.5 (model assignment), Seedance 2.0 (model assignment), S12 - Chorus Hero Shot (+20 more)

### Community 4 - "Comic Panels and Generation Defaults"
Cohesion: 0.09
Nodes (27): character_ref Consistency Anchor, Panel Generation Defaults, Negative Prompt, P01 — Wide Establishing, Darkened Stage, P02 — Lights Snap On, Confident Smirk, P03 — Hair Flip on Beat Drop, P08 — LIVE AI Splash Panel, P09 — Wink Inset with Peace Sign (+19 more)

### Community 5 - "Beat Grid and Audio Measurement"
Cohesion: 0.14
Nodes (23): TXXX:AIGC ID3 Disclosure Tag, scripts/analyze_audio.py, 60-Bar Grid, Measured Beatmap (beatmap.json), Hard Cut 129.54s - Outro Collapse, Hard Cut 132.90s - Final Transient Peak, Hard Cut Points, Onset-Comb Tempo Search (+15 more)

### Community 6 - "LlamaGen MCP Integration"
Cohesion: 0.22
Nodes (11): scripts/connect_mcp.sh, create_comic_generation (MCP tool), Phantom scripts/generate.py Reference in panels.json $comment, Generation Guardrails (credit floor 5000), get_comic_api_usage (MCP tool), get_comic_generation_status (MCP tool), --header Variadic Argument Pitfall, LlamaGen Comic MCP (+3 more)

### Community 7 - "Audio Analysis Internals"
Cohesion: 0.33
Nodes (8): boundaries(), decode(), main(), MP3 -> mono float32 PCM at SR, via the bundled ffmpeg., Comb-filter search: find the BPM+phase whose grid best hits onsets., Checkerboard novelty over a cosine self-similarity matrix., stft(), tempo_grid()

### Community 8 - "Hologram Doubt Sequence"
Cohesion: 0.31
Nodes (9): Section: Pre-chorus (bar 17), Section: Verse 1B (bar 14), S08 - Holographic Billboard Reveal, S09 - Hologram Glitch Insert, S10 - Reaching for the Fracturing Hologram, S11 - Fist Closes, Riser Peaks, LUNA Identity Arc (sleep to doubt to resolve to return), S08 — Hologram Billboard Reveal (+1 more)

### Community 9 - "Prompt Compiler Internals"
Cohesion: 0.53
Nodes (5): build_prompt(), load(), main(), panel_hash(), Assemble the 4-element prompt: character, emotion, action/camera, style.

### Community 10 - "Verse Narrative Comic Page"
Cohesion: 0.60
Nodes (5): P04 — Neon City Street Walk, P05 — Holographic Billboard Reveal, P06 — Hologram Glitch, Is That Really Me, P07 — Clenched Fist, Resolve Returns, Page 2 — Verse / Narrative (0:20-0:55)

## Ambiguous Edges - Review These
- `Generation Guardrails (credit floor 5000)` → `Per-Shot Multi-Model Assignment`  [AMBIGUOUS]
  CLAUDE.md · relation: conceptually_related_to
- `Bar-Line Alignment Rule` → `Kling 3.0 (model assignment)`  [AMBIGUOUS]
  luna-comic/storyboard/shots.json · relation: conceptually_related_to
- `S24 - Final Pose and CSFCCA Logo Flare` → `CSFCCA LIVE AI (ALL_NEW.mp3)`  [AMBIGUOUS]
  luna-comic/storyboard/shots.json · relation: references

## Knowledge Gaps
- **31 isolated node(s):** `connect_mcp.sh script`, `get_comic_generation_status (MCP tool)`, `search_llamagen_docs (MCP tool)`, `LLAMAGEN_API_TOKEN`, `Costume Keyword Lock (purple ponytail, white crop top, chains)` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 38 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Generation Guardrails (credit floor 5000)` and `Per-Shot Multi-Model Assignment`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Bar-Line Alignment Rule` and `Kling 3.0 (model assignment)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `S24 - Final Pose and CSFCCA Logo Flare` and `CSFCCA LIVE AI (ALL_NEW.mp3)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `Per-Shot Multi-Model Assignment` connect `Chorus Shots and Model Assignment` to `Project Architecture and Assets`, `LlamaGen MCP Integration`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `Kling 3.0 (model assignment)` connect `Song Sections and Narrative Shots` to `Hologram Doubt Sequence`, `Chorus Shots and Model Assignment`, `Beat Grid and Audio Measurement`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `S24 - Final Pose and CSFCCA Logo Flare` connect `Beat Grid and Audio Measurement` to `Song Sections and Narrative Shots`, `Chorus Shots and Model Assignment`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Nine-Panel Expression Grid` (e.g. with `LUNA Expression Reference Set (nine emotions)` and `Character Consistency Anchor for Generation`) actually correct?**
  _`Nine-Panel Expression Grid` has 3 INFERRED edges - model-reasoned connections that need verification._