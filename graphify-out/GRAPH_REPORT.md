# Graph Report - futuremode_2026_hackathon  (2026-09-05)

## Corpus Check
- Corpus is ~33,128 words - fits in a single context window. You may not need a graph.

## Summary
- 336 nodes · 542 edges · 15 communities
- Extraction: 81% EXTRACTED · 17% INFERRED · 2% AMBIGUOUS · INFERRED: 94 edges (avg confidence: 0.85)
- Token cost: 337,674 input · 0 output

## Community Hubs (Navigation)
- build_prompts.py
- Song Timeline & Panel Storyboard
- build_shots.py
- Project Manifest & Generation Settings
- Bass Drop Shots & Caption Rules
- Panel Generation Defaults
- Nine-Panel Expression Grid
- Per-Shot Multi-Model Assignment
- Page 3 — Chorus / Explosion (0:55-1:30)
- Verse 2 Quiet Shots
- Character Consistency (top project risk)
- storyboard/beatmap.json (measured beat grid)
- Page 1 — Intro / Standby (0:00-0:20)
- Page 2 — Verse / Narrative (0:20-0:55)
- LlamaGen Comic MCP

## God Nodes (most connected - your core abstractions)
1. `Editable 24-Shot Video Storyboard` - 26 edges
2. `Forced-Aligned Lyric Timeline (32 lines)` - 21 edges
3. `106 BPM / 60-Bar Tempo Grid` - 16 edges
4. `LUNA (virtual idol character)` - 16 edges
5. `Nine-Panel Expression Grid` - 15 edges
6. `LUNA Character Sheet (reference asset)` - 15 edges
7. `《CSFCCA LIVE AI》歌詞全文（未分行、無時間碼）` - 11 edges
8. `LUNA Character Design Sheet (動畫_女生_LUNA)` - 11 edges
9. `Manga Panel Storyboard (13 panels / 4 pages)` - 9 edges
10. `LUNA《CSFCCA LIVE AI》分鏡腳本（24 顆 / 2:14 / 106 BPM / 60 小節）` - 9 edges

## Surprising Connections (you probably didn't know these)
- `「分鏡 × 參考圖 × Prompt」對照表（C01–C03 範本）` --semantically_similar_to--> `shots.json — 24 顆鏡頭 16:9（唯一手編來源）`  [INFERRED] [semantically similar]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md → luna-comic/README.md
- `倒數動機「3、2、1」（重啟／開場記號）` --conceptually_related_to--> `S03 — Eyes Open on the Bass Entry (0:11.81)`  [INFERRED]
  歌詞.txt → luna-comic/storyboard/STORYBOARD.md
- `品牌收尾標語「CSF CCA Live AI」` --conceptually_related_to--> `S24 — Final Freeze Pose and CSFCCA Logo at 2:12.90`  [INFERRED]
  歌詞.txt → luna-comic/storyboard/STORYBOARD.md
- `歌詞主題句「從第一個 prompt 到最後一個鏡頭，每次生成都是新的宇宙」` --semantically_similar_to--> `Prompt 四要素結構（角色描述／情緒表情／動作運鏡／風格氛圍）`  [INFERRED] [semantically similar]
  歌詞.txt → graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md
- `《CSFCCA LIVE AI》歌詞全文（未分行、無時間碼）` --semantically_similar_to--> `歌曲.mp3 的 ASR 逐字稿（品質劣化）`  [INFERRED] [semantically similar]
  歌詞.txt → graphify-out/transcripts/歌曲.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Audio-to-Storyboard Pipeline** — claude_csfcca_live_ai_track, claude_analyze_audio_py, claude_beatmap_json, claude_shots_json, luna_comic_storyboard_storyboard_md [EXTRACTED 1.00]
- **Character Consistency Mechanism** — claude_character_ref, claude_locked_keywords, claude_nine_expressions, claude_hero_shot_reference_workflow, luna_comic_storyboard_storyboard_max_shot_length_9_1s, claude_character_sheet [EXTRACTED 1.00]
- **LlamaGen Generation Guardrail Flow** — claude_generation_guardrails, claude_get_comic_api_usage, claude_create_comic_generation, claude_get_comic_generation_status, claude_llamagen_comic_mcp [EXTRACTED 1.00]
- **LUNA Costume and Silhouette Design System** — luna_comic_assets_reference_luna_character_sheet_purple_braided_ponytail, luna_comic_assets_reference_luna_character_sheet_white_zip_crop_top, luna_comic_assets_reference_luna_character_sheet_white_cargo_miniskirt, luna_comic_assets_reference_luna_character_sheet_silver_chain_accessories, luna_comic_assets_reference_luna_character_sheet_white_platform_sneakers, luna_comic_assets_reference_luna_character_sheet_purple_white_palette [EXTRACTED 1.00]
- **LUNA Nine-Emotion Range Reference** — luna_comic_assets_reference_luna_character_sheet_expression_calm, luna_comic_assets_reference_luna_character_sheet_expression_happy, luna_comic_assets_reference_luna_character_sheet_expression_playful_wink, luna_comic_assets_reference_luna_character_sheet_expression_surprised, luna_comic_assets_reference_luna_character_sheet_expression_shy, luna_comic_assets_reference_luna_character_sheet_expression_angry, luna_comic_assets_reference_luna_character_sheet_expression_aggrieved, luna_comic_assets_reference_luna_character_sheet_expression_thinking, luna_comic_assets_reference_luna_character_sheet_expression_confident_smile [EXTRACTED 1.00]
- **LUNA Turnaround Angle Set** — luna_comic_assets_reference_luna_character_sheet_full_body_turnaround, luna_comic_assets_reference_luna_character_sheet_three_quarter_view, luna_comic_assets_reference_luna_character_sheet_side_profile_view [EXTRACTED 1.00]

## Communities (15 total, 0 thin omitted)

### Community 9 - "build_prompts.py"
Cohesion: 0.53
Nodes (5): build_prompt(), load(), main(), panel_hash(), Assemble the 4-element prompt: character, emotion, action/camera, style.

### Community 0 - "Song Timeline & Panel Storyboard"
Cohesion: 0.08
Nodes (53): anchor_for(), assign(), attach_to_shots(), load(), main(), snap(), split_lines(), to_srt() (+45 more)

### Community 8 - "build_shots.py"
Cohesion: 0.31
Nodes (9): build_prompt(), compile_shots(), load(), main(), shot_hash(), to_markdown(), Assemble the 5-element video prompt., Same rule as build_prompts.py: only re-render what actually changed. (+1 more)

### Community 7 - "Project Manifest & Generation Settings"
Cohesion: 0.13
Nodes (18): boundaries(), decode(), main(), stft(), tempo_grid(), MP3 -> mono float32 PCM at SR, via the bundled ffmpeg., Comb-filter search: find the BPM+phase whose grid best hits onsets., Checkerboard novelty over a cosine self-similarity matrix. (+10 more)

### Community 11 - "Bass Drop Shots & Caption Rules"
Cohesion: 0.27
Nodes (5): connect_mcp.sh script, 段落 Build 0:11.8–0:20.9（貝斯進場 +5.5 dB，全曲第一個衝擊點）, S05 0:16.3–0:20.9 舞蹈 hook，環繞 90 度（字卡與字幕衝突鏡）, 字卡／歌詞卡以剪輯軟體疊加，不由 AI 模型生成, 字卡與歌詞字幕分離規則

### Community 12 - "Panel Generation Defaults"
Cohesion: 0.21
Nodes (8): Panel Generation Defaults, Panel Status Lifecycle (pending to queued to done/failed), 段落 Verse 1 0:20.9–0:36.7（低頻退到 0.62x，人聲帶撐起）, S06 0:20.9–0:25.4 霓虹濕街側面跟拍, S07 0:25.4–0:29.9 臉部特寫，淺景深手持, Negative Prompt, Style Suffix (Panel Prompt Tail), character_ref Consistency Anchor

### Community 1 - "Nine-Panel Expression Grid"
Cohesion: 0.04
Nodes (65): scripts/align_lyrics.py — 歌詞＋beatmap → lyrics/ 與 lyric_lines, scripts/analyze_audio.py — 歌曲.mp3 → beatmap 數值, scripts/build_prompts.py — panels.json 編譯器（legacy）, scripts/build_shots.py — shots.json 編譯器（影片軌）, 開場意象「一張空白的畫面，等著第一束光出現」, 倒數動機「3、2、1」（重啟／開場記號）, 品牌收尾標語「CSF CCA Live AI」, 英文橋段「Create it, make it, show me your world / Dream it, build it, let the future unfold」 (+57 more)

### Community 3 - "Per-Shot Multi-Model Assignment"
Cohesion: 0.05
Nodes (55): S01 — Closed-Eye Close-Up in Darkness, S03 — Eyes Open on the Bass Entry (0:11.81), S20 — Low End Vanishes, Single Top Light, S21 — Eye Close-Up, Decision Made, Cut to Black, S24 — Final Freeze Pose and CSFCCA Logo at 2:12.90, S04 — Stage Lights Explode on Bass Drop, S08 — Hologram Billboard Reveal, S09 — Hologram Glitch Stinger (+47 more)

### Community 13 - "Page 3 — Chorus / Explosion (0:55-1:30)"
Cohesion: 0.27
Nodes (6): 段落 Pre-chorus 0:36.7–0:45.8（空氣頻段爬升 riser）, S10 0:36.7–0:41.2 觸碰碎裂全息 · 字卡「那真的是我嗎？」, P08 — LIVE AI Splash Panel, P09 — Wink Inset with Peace Sign, P10 — Back View of Light-Stick Crowd, Page 3 — Chorus / Explosion (0:55-1:30)

### Community 14 - "Verse 2 Quiet Shots"
Cohesion: 0.67
Nodes (3): 段落 Verse 2 1:15.2–1:24.3（中頻收到 0.90x）, S18 1:15.2–1:19.7 橫向緩軌，空舞台一盞暖光, S19 1:19.7–1:24.3 柔焦特寫，私人的小微笑

### Community 2 - "Character Consistency (top project risk)"
Cohesion: 0.06
Nodes (38): Anime/Manga Cel-Shaded Art Style, Chunky White Platform Sneakers, Four Captioned Pose Panels, Site Navigation Bar (LIVE AI / WORKSHOP / CONTENT IRP / GLOBAL EXCHANGE / PARTNER), Y2K Streetwear Idol Silhouette, Tagline: 準備好了！下一個舞台，交給我吧！, Thigh Strap, Chain Accessories and Stacked Bracelets, Trait: 有魅力 (Charismatic) — 自然吸引眾人目光，擅長與人互動 (+30 more)

### Community 5 - "storyboard/beatmap.json (measured beat grid)"
Cohesion: 0.08
Nodes (21): LUNA — LIVE AI Comic Project, 副歌「Live AI，現在就創造未來，讓想像穿越畫面之外」, 階段二：完整版 MV 3–4 分鐘（25–40 顆鏡頭）, 段落 Final chorus 1:33.3–1:58.2（novelty 0.86 全曲最高）, S16 1:06.2–1:10.7 背面大遠景，面向應援棒海洋, S23 1:42.4–1:58.2 副歌多角度組，每 2 小節一切（15.8s，內部 7 切點）, 以第一顆定裝鏡頭作為後續共同參考圖, 階段一：短版預告 15–30 秒（3–5 顆鏡頭） (+13 more)

### Community 4 - "Page 1 — Intro / Standby (0:00-0:20)"
Cohesion: 0.08
Nodes (29): Art Style: Clean-Line Anime Cel Illustration on Cream Ground, Catchphrase: 準備好了！下一個舞台，交給我吧！, Visual Attribute: Silver Chains, Thigh Strap, Stacked Bracelets, CSFCCA 科幻文創 (Science Fiction and Cultural & Creative Association), Nine-Expression Sheet (平靜/開心/俏皮眨眼/驚訝/害羞/生氣/委屈/思考/自信微笑), Full-Body Reference Pose, LIVE AI (Brand / Program Line), 個性總結 Personality Summary Block (+21 more)

### Community 10 - "Page 2 — Verse / Narrative (0:20-0:55)"
Cohesion: 0.60
Nodes (5): P04 — Neon City Street Walk, P05 — Holographic Billboard Reveal, P06 — Hologram Glitch, Is That Really Me, P07 — Clenched Fist, Resolve Returns, Page 2 — Verse / Narrative (0:20-0:55)

### Community 6 - "LlamaGen Comic MCP"
Cohesion: 0.22
Nodes (11): scripts/connect_mcp.sh, create_comic_generation (MCP tool), get_comic_api_usage (MCP tool), get_comic_generation_status (MCP tool), search_llamagen_docs (MCP tool), LlamaGen Comic MCP, LLAMAGEN_API_TOKEN, One-Time LlamaGen MCP Registration (+3 more)

## Ambiguous Edges - Review These
- `Section: Intro (bar 1)` → `Page 1 — Intro / Standby`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references
- `Section: Verse 1A (bar 10)` → `Page 2 — Verse / Narrative`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references
- `Section: Chorus 1 ext. (bar 26)` → `Page 3 — Chorus / Explosion`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references
- `Section: Outro (bar 58)` → `Page 4 — Bridge & Outro`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references
- `LUNA《CSFCCA LIVE AI》分鏡腳本（24 顆 / 2:14 / 106 BPM / 60 小節）` → `階段二：完整版 MV 3–4 分鐘（25–40 顆鏡頭）`  [AMBIGUOUS]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md · relation: conceptually_related_to
- `ASR 誤聽與重複迴圈（「尋浩洋季」「帥銀口」「prone」與大量重複的 girl）` → `歌詞時間碼為估算而非實測`  [AMBIGUOUS]
  graphify-out/transcripts/歌曲.txt · relation: conceptually_related_to
- `CSFCCA (科幻文創 Science Fiction and Cultural Creative Association)` → `Rationale: Sheet as Visual Consistency Reference for Generation`  [AMBIGUOUS]
  luna-comic/assets/reference/luna_character_sheet.jpg · relation: conceptually_related_to
- `LlamaGen Comic MCP（search_llamagen_docs / get_comic_api_usage / create_comic_generation / get_comic_generation_status）` → `自架 ComfyUI MiniMax H3（S01–S24 統一模型）`  [AMBIGUOUS]
  luna-comic/storyboard/STORYBOARD.md · relation: conceptually_related_to
- `Visual Attribute: Silver Chains, Thigh Strap, Stacked Bracelets` → `Trait: 獨立 (Independent / Self-Reliant, Walks Own Path)`  [AMBIGUOUS]
  動畫_女生_LUNA.jpg · relation: conceptually_related_to
- `Per-Shot Multi-Model Assignment` → `Generation Guardrails (credit floor 5000)`  [AMBIGUOUS]
  CLAUDE.md · relation: conceptually_related_to

## Knowledge Gaps
- **50 isolated node(s):** `connect_mcp.sh script`, `英文橋段「Create it, make it, show me your world / Dream it, build it, let the future unfold」`, `Hook「Live AI / Li-Li-Live A-AI」`, `段落 Climax 1:58.2–2:09.5（全曲最大聲，低頻 1.6x）`, `段落 Outro 2:09.5–2:14.3（低頻崩落，2:12 最後 transient 0.96）` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 69 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Section: Intro (bar 1)` and `Page 1 — Intro / Standby`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Section: Verse 1A (bar 10)` and `Page 2 — Verse / Narrative`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Section: Chorus 1 ext. (bar 26)` and `Page 3 — Chorus / Explosion`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Section: Outro (bar 58)` and `Page 4 — Bridge & Outro`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `LUNA《CSFCCA LIVE AI》分鏡腳本（24 顆 / 2:14 / 106 BPM / 60 小節）` and `階段二：完整版 MV 3–4 分鐘（25–40 顆鏡頭）`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `ASR 誤聽與重複迴圈（「尋浩洋季」「帥銀口」「prone」與大量重複的 girl）` and `歌詞時間碼為估算而非實測`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CSFCCA (科幻文創 Science Fiction and Cultural Creative Association)` and `Rationale: Sheet as Visual Consistency Reference for Generation`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._