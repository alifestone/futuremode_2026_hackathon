# Graph Report - futuremode_2026_hackathon  (2026-09-05)

## Corpus Check
- Corpus is ~34,360 words - fits in a single context window. You may not need a graph.

## Summary
- 251 nodes · 389 edges · 16 communities (15 shown, 1 thin omitted)
- Extraction: 81% EXTRACTED · 17% INFERRED · 2% AMBIGUOUS · INFERRED: 65 edges (avg confidence: 0.84)
- Token cost: 257,410 input · 0 output

## Community Hubs (Navigation)
- Song Timeline & Panel Storyboard
- Lyrics, Compilers & Data Provenance
- Luna Character Sheet Reference
- MV Production Plan & Consistency Risk
- Luna Visual Identity & Personality
- Chorus Shots & Costume-Lock Strategy
- Lyric Alignment Script
- Project Manifest & Generation Settings
- Shot Compiler (Video Track)
- Audio Analysis Script
- Panel Prompt Compiler (Legacy)
- Bass Drop Shots & Caption Rules
- Verse 1 Hologram Shots
- Pre-chorus Riser Shots
- Verse 2 Quiet Shots
- LlamaGen MCP Registration

## God Nodes (most connected - your core abstractions)
1. `Editable 24-Shot Video Storyboard` - 26 edges
2. `Forced-Aligned Lyric Timeline (32 lines)` - 21 edges
3. `106 BPM / 60-Bar Tempo Grid` - 16 edges
4. `Nine-Expression Reference Grid` - 12 edges
5. `《CSFCCA LIVE AI》歌詞全文（未分行、無時間碼）` - 11 edges
6. `Luna (Virtual Idol Character)` - 11 edges
7. `LUNA Character Design Sheet (動畫_女生_LUNA)` - 11 edges
8. `Luna Character Sheet (LIVE AI LUNA)` - 10 edges
9. `LUNA《CSFCCA LIVE AI》分鏡腳本（24 顆 / 2:14 / 106 BPM / 60 小節）` - 9 edges
10. `Manga Panel Storyboard (13 panels / 4 pages)` - 9 edges

## Surprising Connections (you probably didn't know these)
- `「分鏡 × 參考圖 × Prompt」對照表（C01–C03 範本）` --semantically_similar_to--> `shots.json — 24 顆鏡頭 16:9（唯一手編來源）`  [INFERRED] [semantically similar]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md → luna-comic/README.md
- `角色 LoRA 訓練（一致性強化選項）` --semantically_similar_to--> `character_ref ＋ locked_keywords 一致性鎖`  [INFERRED] [semantically similar]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md → luna-comic/README.md
- `Face-lock / Character ID（如 Higgsfield Soul ID）` --semantically_similar_to--> `character_ref ＋ locked_keywords 一致性鎖`  [INFERRED] [semantically similar]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md → luna-comic/README.md
- `字卡／歌詞卡以剪輯軟體疊加，不由 AI 模型生成` --semantically_similar_to--> `字卡與歌詞字幕分離規則`  [INFERRED] [semantically similar]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md → luna-comic/README.md
- `預留 20–30% 預算／點數作為重試緩衝` --semantically_similar_to--> `生成前的點數護欄（<5,000 停手）`  [INFERRED] [semantically similar]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md → luna-comic/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **shots.json 編輯→編譯→只重生成變動鏡頭的循環** — luna_comic_readme_shots_json, luna_comic_readme_build_shots_py, luna_comic_readme_project_json, luna_comic_readme_single_editable_source, luna_comic_readme_consistency_lock, luna_comic_storyboard_storyboard_storyboard [EXTRACTED 1.00]
- **角色一致性對策集合（設定圖／定裝鏡／服裝關鍵字／表情九宮格／LoRA／Face-lock）** — luna_comic_readme_luna_character_sheet, luna_comic_storyboard_storyboard_costume_test_shot, luna_comic_storyboard_storyboard_costume_lock_keywords, luna_comic_storyboard_storyboard_expression_grid_8_of_9, luna_comic_storyboard_storyboard_max_shot_length, graphify_out_converted_luna_mv_zhizuojihuashu_ee70e4e1_character_lora, graphify_out_converted_luna_mv_zhizuojihuashu_ee70e4e1_face_lock_soul_id, graphify_out_converted_luna_mv_zhizuojihuashu_ee70e4e1_consistency_risk [INFERRED 0.85]
- **以實測音訊驅動的卡點鏈（分析→節拍格線→六個硬切→對應鏡頭）** — luna_comic_readme_analyze_audio_py, luna_comic_readme_beatmap_json, luna_comic_storyboard_storyboard_beat_grid, luna_comic_storyboard_storyboard_hard_cuts, luna_comic_storyboard_storyboard_s04, luna_comic_storyboard_storyboard_s12, luna_comic_storyboard_storyboard_s22, luna_comic_storyboard_storyboard_s24 [EXTRACTED 1.00]
- **Luna Visual Identity: Hair, Outfit, Accessories, Footwear, Palette** — luna_comic_assets_reference_luna_character_sheet_luna, luna_comic_assets_reference_luna_character_sheet_purple_braided_ponytail, luna_comic_assets_reference_luna_character_sheet_white_zip_crop_top, luna_comic_assets_reference_luna_character_sheet_white_cargo_miniskirt, luna_comic_assets_reference_luna_character_sheet_thigh_strap_and_bracelets, luna_comic_assets_reference_luna_character_sheet_platform_sneakers, luna_comic_assets_reference_luna_character_sheet_white_purple_palette [EXTRACTED 1.00]
- **Nine-Expression Emotional Range Set** — luna_comic_assets_reference_luna_character_sheet_expression_calm, luna_comic_assets_reference_luna_character_sheet_expression_happy, luna_comic_assets_reference_luna_character_sheet_expression_playful_wink, luna_comic_assets_reference_luna_character_sheet_expression_surprised, luna_comic_assets_reference_luna_character_sheet_expression_shy, luna_comic_assets_reference_luna_character_sheet_expression_angry, luna_comic_assets_reference_luna_character_sheet_expression_aggrieved, luna_comic_assets_reference_luna_character_sheet_expression_thinking, luna_comic_assets_reference_luna_character_sheet_expression_confident_smile [EXTRACTED 1.00]
- **Five-Trait Personality Profile Driving Poses and Expressions** — luna_comic_assets_reference_luna_character_sheet_trait_lively, luna_comic_assets_reference_luna_character_sheet_trait_charismatic, luna_comic_assets_reference_luna_character_sheet_trait_confident, luna_comic_assets_reference_luna_character_sheet_trait_playful, luna_comic_assets_reference_luna_character_sheet_trait_independent, luna_comic_assets_reference_luna_character_sheet_pose_panel_set [INFERRED 0.85]
- **LUNA Character Bible: full-body reference + attitude panels + expression sheet + personality summary** — donghua_nvsheng_luna_character_sheet, donghua_nvsheng_luna_full_body_turnaround, donghua_nvsheng_luna_pose_panels, donghua_nvsheng_luna_expression_sheet, donghua_nvsheng_luna_personality_summary [EXTRACTED 1.00]
- **Five-Trait Personality Profile (活潑/有魅力/自信/俏皮/獨立)** — donghua_nvsheng_luna_trait_lively, donghua_nvsheng_luna_trait_charismatic, donghua_nvsheng_luna_trait_confident, donghua_nvsheng_luna_trait_playful, donghua_nvsheng_luna_trait_independent, donghua_nvsheng_luna_luna [EXTRACTED 1.00]
- **LUNA Visual Identity: purple braided ponytail + white streetwear + chain accessories in an anime cel style** — donghua_nvsheng_luna_purple_braided_ponytail, donghua_nvsheng_luna_white_streetwear_outfit, donghua_nvsheng_luna_chain_accessories, donghua_nvsheng_luna_anime_cel_style, donghua_nvsheng_luna_purple_white_palette [INFERRED 0.85]
- **Measured 106 BPM Grid as Shared Timing Spine** — luna_comic_storyboard_beatmap_measured_audio, luna_comic_storyboard_beatmap_tempo_grid, luna_comic_lyrics_lyrics_forced_alignment, luna_comic_storyboard_shots_storyboard, luna_comic_storyboard_shots_bar_line_lock [EXTRACTED 1.00]
- **LUNA Visual Consistency Lock Across Both Renderings** — luna_comic_project_luna_character, luna_comic_project_locked_keywords, luna_comic_project_expression_set, luna_comic_project_character_reference_sheet, luna_comic_panels_panels_defaults, luna_comic_storyboard_shots_defaults [INFERRED 0.95]
- **Signal-Driven Hard-Cut Spine of the Edit** — luna_comic_storyboard_beatmap_hard_cut_points, luna_comic_storyboard_shots_s04, luna_comic_storyboard_shots_s12, luna_comic_storyboard_shots_s20, luna_comic_storyboard_shots_s22, luna_comic_storyboard_shots_s24b [EXTRACTED 1.00]

## Communities (16 total, 1 thin omitted)

### Community 0 - "Song Timeline & Panel Storyboard"
Cohesion: 0.11
Nodes (42): Forced-Aligned Lyric Timeline (32 lines), Lyrics Readability Grid (mirrored tempo), Manga Panel Storyboard (13 panels / 4 pages), Page 1 — Intro / Standby, Page 2 — Verse / Narrative, Page 3 — Chorus / Explosion, Page 4 — Bridge & Outro, Panel Status Lifecycle (pending → queued → done/failed) (+34 more)

### Community 1 - "Lyrics, Compilers & Data Provenance"
Cohesion: 0.08
Nodes (38): 開場意象「一張空白的畫面，等著第一束光出現」, 倒數動機「3、2、1」（重啟／開場記號）, 品牌收尾標語「CSF CCA Live AI」, 英文橋段「Create it, make it, show me your world / Dream it, build it, let the future unfold」, Hook「Live AI / Li-Li-Live A-AI」, 歌詞主題句「從第一個 prompt 到最後一個鏡頭，每次生成都是新的宇宙」, 《CSFCCA LIVE AI》歌詞全文（未分行、無時間碼）, 音樂卡點與影像同步規劃（BPM 標記，每 1–2 小節換鏡） (+30 more)

### Community 2 - "Luna Character Sheet Reference"
Cohesion: 0.09
Nodes (37): Luna Character Sheet (LIVE AI LUNA), Anime/Manga Cel-Shaded Art Style, CSFCCA (科幻文創 Science Fiction and Cultural & Creative Association), Expression: 委屈 (Aggrieved / Sulking), Expression: 生氣 (Angry), Expression: 平靜 (Calm), Expression: 自信微笑 (Confident Smile), Nine-Expression Reference Grid (+29 more)

### Community 3 - "MV Production Plan & Consistency Risk"
Cohesion: 0.09
Nodes (28): 預留 20–30% 預算／點數作為重試緩衝, 角色 LoRA 訓練（一致性強化選項）, 現有角色設定圖素材包（全身立繪＋4 情境圖＋9 表情模組＋個性關鍵字）, 後期統一調色為必要步驟（DaVinci Resolve / Premiere）, AI 影片生成的角色一致性限制（本案最大風險）, 九宮格表情模組（平靜／開心／俏皮眨眼／驚訝／害羞／生氣／委屈／思考／自信微笑）, Face-lock / Character ID（如 Higgsfield Soul ID）, 製作流程五大階段（前期／一致性素材補強／AI 影片生成／後期合成／音樂剪輯同步） (+20 more)

### Community 4 - "Luna Visual Identity & Personality"
Cohesion: 0.13
Nodes (22): Art Style: Clean-Line Anime Cel Illustration on Cream Ground, Catchphrase: 準備好了！下一個舞台，交給我吧！, Visual Attribute: Silver Chains, Thigh Strap, Stacked Bracelets, LUNA Character Design Sheet (動畫_女生_LUNA), CSFCCA 科幻文創 (Science Fiction and Cultural & Creative Association), Nine-Expression Sheet (平靜/開心/俏皮眨眼/驚訝/害羞/生氣/委屈/思考/自信微笑), Full-Body Reference Pose, LIVE AI (Brand / Program Line) (+14 more)

### Community 5 - "Chorus Shots & Costume-Lock Strategy"
Cohesion: 0.12
Nodes (17): 副歌「Live AI，現在就創造未來，讓想像穿越畫面之外」, 以第一顆定裝鏡頭作為後續共同參考圖, 階段一：短版預告 15–30 秒（3–5 顆鏡頭）, 階段二：完整版 MV 3–4 分鐘（25–40 顆鏡頭）, 段落 Chorus 1 + 延伸 0:45.8–1:15.2（中頻 1.32x，持續高能）, 定裝鏡策略（先產 S12，通過後當其餘鏡頭參考圖）, 段落 Final chorus 1:33.3–1:58.2（novelty 0.86 全曲最高）, 單顆鏡頭上限 9.1 秒（S15、S22） (+9 more)

### Community 6 - "Lyric Alignment Script"
Cohesion: 0.26
Nodes (12): anchor_for(), assign(), attach_to_shots(), load(), main(), Snap a time to the nearest bar line, so every cue lands on the grid., Lay lines onto the bar grid, section by section., Fill each shot's lyric_lines with the ids of lines overlapping it. (+4 more)

### Community 7 - "Project Manifest & Generation Settings"
Cohesion: 0.24
Nodes (11): Panel Generation Defaults (3:4 manga), luna_character_sheet.jpg Consistency Anchor, ComfyUI MiniMax H3 Video Backend, 5000-Credit Floor Guard, Nine Canonical LUNA Expressions, LlamaGen MCP Image Generation Provider, LUNA Locked Costume Keywords, LUNA (character definition) (+3 more)

### Community 8 - "Shot Compiler (Video Track)"
Cohesion: 0.31
Nodes (9): build_prompt(), compile_shots(), load(), main(), Assemble the 5-element video prompt., Same rule as build_prompts.py: only re-render what actually changed., Group by model — the batches you actually paste, one interface at a time., shot_hash() (+1 more)

### Community 9 - "Audio Analysis Script"
Cohesion: 0.33
Nodes (8): boundaries(), decode(), main(), MP3 -> mono float32 PCM at SR, via the bundled ffmpeg., Comb-filter search: find the BPM+phase whose grid best hits onsets., Checkerboard novelty over a cosine self-similarity matrix., stft(), tempo_grid()

### Community 10 - "Panel Prompt Compiler (Legacy)"
Cohesion: 0.53
Nodes (5): build_prompt(), load(), main(), panel_hash(), Assemble the 4-element prompt: character, emotion, action/camera, style.

### Community 11 - "Bass Drop Shots & Caption Rules"
Cohesion: 0.40
Nodes (5): 字卡／歌詞卡以剪輯軟體疊加，不由 AI 模型生成, 字卡與歌詞字幕分離規則, 段落 Build 0:11.8–0:20.9（貝斯進場 +5.5 dB，全曲第一個衝擊點）, S04 0:11.8–0:16.3 低頻炸開，舞台燈同時亮起, S05 0:16.3–0:20.9 舞蹈 hook，環繞 90 度（字卡與字幕衝突鏡）

### Community 12 - "Verse 1 Hologram Shots"
Cohesion: 0.50
Nodes (5): S06 0:20.9–0:25.4 霓虹濕街側面跟拍, S07 0:25.4–0:29.9 臉部特寫，淺景深手持, S08 0:29.9–0:34.5 過肩變焦，巨型全息看板播她自己的臉, S09 0:34.5–0:36.7 全息崩壞，掃描線撕裂（一小節 stinger）, 段落 Verse 1 0:20.9–0:36.7（低頻退到 0.62x，人聲帶撐起）

### Community 13 - "Pre-chorus Riser Shots"
Cohesion: 0.67
Nodes (3): 段落 Pre-chorus 0:36.7–0:45.8（空氣頻段爬升 riser）, S10 0:36.7–0:41.2 觸碰碎裂全息 · 字卡「那真的是我嗎？」, S11 0:41.2–0:45.8 握拳聚能，riser 頂點甩鏡出

### Community 14 - "Verse 2 Quiet Shots"
Cohesion: 0.67
Nodes (3): S18 1:15.2–1:19.7 橫向緩軌，空舞台一盞暖光, S19 1:19.7–1:24.3 柔焦特寫，私人的小微笑, 段落 Verse 2 1:15.2–1:24.3（中頻收到 0.90x）

## Ambiguous Edges - Review These
- `LlamaGen Comic MCP（search_llamagen_docs / get_comic_api_usage / create_comic_generation / get_comic_generation_status）` → `自架 ComfyUI MiniMax H3（S01–S24 統一模型）`  [AMBIGUOUS]
  luna-comic/storyboard/STORYBOARD.md · relation: conceptually_related_to
- `歌詞時間碼為估算而非實測` → `ASR 誤聽與重複迴圈（「尋浩洋季」「帥銀口」「prone」與大量重複的 girl）`  [AMBIGUOUS]
  graphify-out/transcripts/歌曲.txt · relation: conceptually_related_to
- `LUNA《CSFCCA LIVE AI》分鏡腳本（24 顆 / 2:14 / 106 BPM / 60 小節）` → `階段二：完整版 MV 3–4 分鐘（25–40 顆鏡頭）`  [AMBIGUOUS]
  graphify-out/converted/LUNA_MV_製作計畫書_ee70e4e1.md · relation: conceptually_related_to
- `CSFCCA (科幻文創 Science Fiction and Cultural & Creative Association)` → `Rationale: Sheet as Visual Consistency Reference for Generation`  [AMBIGUOUS]
  luna-comic/assets/reference/luna_character_sheet.jpg · relation: conceptually_related_to
- `Trait: 獨立 (Independent / Self-Reliant, Walks Own Path)` → `Visual Attribute: Silver Chains, Thigh Strap, Stacked Bracelets`  [AMBIGUOUS]
  動畫_女生_LUNA.jpg · relation: conceptually_related_to
- `Section: Intro (bar 1)` → `Page 1 — Intro / Standby`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references
- `Section: Verse 1A (bar 10)` → `Page 2 — Verse / Narrative`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references
- `Section: Chorus 1 ext. (bar 26)` → `Page 3 — Chorus / Explosion`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references
- `Section: Outro (bar 58)` → `Page 4 — Bridge & Outro`  [AMBIGUOUS]
  luna-comic/panels/panels.json · relation: references

## Knowledge Gaps
- **36 isolated node(s):** `connect_mcp.sh script`, `project.json（character bible / style lock / generation settings）`, `scripts/connect_mcp.sh — LlamaGen MCP 一次性註冊`, `段落 Climax 1:58.2–2:09.5（全曲最大聲，低頻 1.6x）`, `段落 Outro 2:09.5–2:14.3（低頻崩落，2:12 最後 transient 0.96）` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 53 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `LlamaGen Comic MCP（search_llamagen_docs / get_comic_api_usage / create_comic_generation / get_comic_generation_status）` and `自架 ComfyUI MiniMax H3（S01–S24 統一模型）`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `歌詞時間碼為估算而非實測` and `ASR 誤聽與重複迴圈（「尋浩洋季」「帥銀口」「prone」與大量重複的 girl）`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `LUNA《CSFCCA LIVE AI》分鏡腳本（24 顆 / 2:14 / 106 BPM / 60 小節）` and `階段二：完整版 MV 3–4 分鐘（25–40 顆鏡頭）`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CSFCCA (科幻文創 Science Fiction and Cultural & Creative Association)` and `Rationale: Sheet as Visual Consistency Reference for Generation`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Trait: 獨立 (Independent / Self-Reliant, Walks Own Path)` and `Visual Attribute: Silver Chains, Thigh Strap, Stacked Bracelets`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Section: Intro (bar 1)` and `Page 1 — Intro / Standby`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Section: Verse 1A (bar 10)` and `Page 2 — Verse / Narrative`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._