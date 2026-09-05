# 設計決策紀錄 — 影片製作 AI workflow app

> 來源：grill-me 深度訪談（2026-09-05）。本文件是雙方確認後的唯一決策權威；
> 若與任何程式碼註解衝突，以本文件為準，並更新程式碼。
>
> 目標專案：以現有 `luna-comic/`（LUNA MV 管線）為基礎，製作一個「影片製作 AI workflow app」。
> 兩個核心痛點：
> 1. **細節缺乏**：human input 沒給不代表不重要（固定場景、細節等），但目前的 harness 不會提示 LLM 規劃這些細節 → 影片細節缺乏、cut 之間不連貫。
> 2. **上下文斷裂**：本地算力不足時把提示詞複製到網頁平台，因缺少上下文而更不一致 → app 必須支援完整上下文匯出，讓單一 cut 匯出完整提示詞，本地執行與匯出拿到**相同上下文**。

---

## 1. 定位與形式（Q1/Q2/Q10）

| # | 決策 | 結論 |
|---|------|------|
| 1.1 | 泛用性 | **引擎化但克制**：歌曲、角色抽象化，但限定 **MV 領域**；不做 plugin 系統 |
| 1.2 | 交付形式 | **markdown 協議 ＋ scripts**，任何 coding agent 照 PROTOCOL.md 即可驅動（agent-executable） |
| 1.3 | 操作面 | **Web UI 是人的主要操作面**（除影片剪輯外的一切操作），與 agent 路徑共存、操作同一份 JSON |
| 1.4 | UI 技術紀律 | Python **stdlib-only** `server.py`（薄殼呼叫 scripts，~200 行）＋ 單一靜態 HTML（vanilla JS，無 build、無框架） |
| 1.5 | UI 操作面清單 | ①專案總覽 ②Items 管理（7 型別分頁、檢查表、改動影響 shots 警示）③分鏡表（含內嵌編輯）④單 cut 檢視（resolved prompt、一鍵複製、下載 ref、clip 預覽）⑤生成控制台（打包→鎖定→批次生成、進度、seed）⑥匯出區（平台封包複製＋context.json 下載） |

## 2. 工作流邊界（Q3）

| # | 決策 | 結論 |
|---|------|------|
| 2.1 | app 擁有 | **④→⑦**：分鏡 → 場景/item 規劃 → 編譯/封包 → 執行/匯出 |
| 2.2 | 不重寫 | beatmap（analyze_audio）與 lyrics（align_lyrics）為外部前製工具，僅在 manifest 引用產物 |
| 2.3 | 剪輯 | `assemble_mv.py` 原樣保留不重寫；**封包攜帶剪輯意圖**（in/out 點依小節線、過場、caption/字幕優先規則） |

## 3. 核心資料模型（Q4/Q5）

| # | 決策 | 結論 |
|---|------|------|
| 3.1 | Registry | 專案根**單一 `items.json`**；每筆 `{id, type, text, locked?, note}` |
| 3.2 | 型別（固定 7 種） | `character`（角色鎖，全鏡必掛）、`state`（世界/角色狀態變量）、`scene`（場景基底）、`set_piece`（固定道具/裝置）、`look`（燈光＋氛圍）、`style`（專案風格鎖，全鏡必掛）、`camera_grammar`（鏡頭語言慣例，可選） |
| 3.3 | 引用 | shot 只存 `items: ["char.luna", "scene.arena_empty", ...]` ID 清單 |
| 3.4 | 編譯順序（決定性） | `character → state → scene → set_piece → look → action/camera/sync → style`；順序是「本地/匯出字串一致」的前提 |
| 3.5 | 變異兩層紀律 | **事實改變 → 新 item 進 registry**（世界事實只有一份）；**強調/追加 → shot 內 `overrides: {item_id: 追加文字}`，compile 附加於基底之後、永不 replace** |
| 3.6 | 連鎖效應 | 改 item 文字 = 所有引用鏡頭的 prompt hash 改變 → diff 報告列出受影響鏡頭，重生成 scope 自動擴大（一致性鎖的預期行為） |
| 3.7 | Hash 基底 | 合併後的 final prompt 字串（沿用現有規則） |

## 4. 完整性契約（Q6/Q11）

| # | 決策 | 結論 |
|---|------|------|
| 4.1 | Facets 檢查表 | 每型別有最小檢查表（= 給 agent 的提示詞）。例：`scene`＝空間類型/尺度/天際線/時段/天氣/色彩基調；`set_piece`＝位置/尺寸/材質/光照反應/互動；`look`＝主光方向/光質/色溫/氛圍/對比；`state`＝觸發時間點/事實/影響 items；`character`＝髮/全身服裝/配件/鞋；`style`＝畫風/片比/調色 |
| 4.2 | Gap report | `plan.py` 輸出缺口 JSON：缺的 item 引用、未填滿的檢查表、沒掛 scene 的 shot — agent 照單補、人照單審 |
| 4.3 | 兩段式門檻 | **草稿（`--draft`）＝只警告**，不擋探索；**`lock`/`export` ＝硬門檻**：任何缺失/引用斷裂/override 目標不存在 → 拒絕編譯匯出 |
| 4.4 | 檢查紀律 | scripts 只做**決定性結構檢查**（引用解析、欄位存在、最小長度）；語意完整性靠 plan pass 的 LLM lint ＋ 人類 diff review（不做脆弱關鍵字檢查） |
| 4.5 | 歌詞耦合 | 有 `lyric_lines` 的鏡頭**必須有「演繹聲明」欄位**（見 5.x），缺了檔匯出 |

## 5. 歌詞↔畫面耦合（Q11）

| # | 決策 | 結論 |
|---|------|------|
| 5.1 | `lyric_intent` 欄位 | 每鏡頭必填（該鏡如何演繹當下歌詞意象），進完整性契約、gap report 檢查 |
| 5.2 | 歌詞原文織入 prompt | 固定位置 `vocal: 「歌詞」— reflect this line's imagery`；H3 text encoder 為 Qwen3VL 原生支援中文，可行性確認 |
| 5.3 | 耦合 lint | plan pass 的 LLM 檢查：action / lyric_intent 與歌詞意象同源（語意檢查，不走決定性 gate） |
| 5.4 | 既有規則 | `caption`（設計字卡）優先於歌詞字幕的規則不變 |
| 5.5 | 延後 | 歌詞驅動嘴型/人聲 = v2（目前音軌仍捨棄、歌曲後期混入） |

## 6. 動態連續性（Q7）

| # | 決策 | 結論 |
|---|------|------|
| 6.1 | v1 | **文字鉤子**：每鏡 `continuity_in` / `continuity_out`（承接上一剪的 pose/方向/畫面對象；交棒下一剪的 pose/位置/視線）— 進契約、進 gap report、進封包，compile 固定位置織入 |
| 6.2 | v2 / opt-in | **接棒幀（chain-ref）**：上一顆實際生成 clip 的最後一幀當 `<Picture 2>` 饋給下一顆（H3 ref 槽位 0–8 已支援）。代價：串行生成、下游 ref 會過期需重鏈 — 進場時機延後 |

## 7. 封包（Q8）

| # | 決策 | 結論 |
|---|------|------|
| 7.1 | 結構 | `out/packages/<CUT_ID>/`：`context.json`（唯一權威）＋ `prompt.txt` ＋ `graph.json` ＋ `ref/` ＋ `MANIFEST.md` |
| 7.2 | context.json 內容 | resolved 最終 prompt、resolved item 文字快照、refs（路徑＋hash）、settings（seed/steps/grid/解析度/片比/fps/時長）、continuity、sync、歌詞、剪輯意圖、`context_hash` |
| 7.3 | 凍結快照語意 | 封包 = 匯出當下上下文的不可變副本；之後改 items.json **不影響已匯出封包**；只有重新 lock/export 才重建並重算 hash |
| 7.4 | 對帳 | run_state 記錄每支 clip 的 context_hash → 一眼看出該 clip 是哪個上下文版本生的 |
| 7.5 | MANIFEST.md 內容 | item 解析表、場景摘錄、設定一覽、剪輯意圖、「本機跑法 vs 貼去網頁」指示；（可選）上一顆 cut 的 continuity_out |

## 8. 平台 adapter（Q12）

| # | 決策 | 結論 |
|---|------|------|
| 8.1 | 原則 | canonical `context.json` → 各平台 render（決定性翻譯器）；本地與網頁消耗同一份權威資料 |
| 8.2 | v1 清單 | ① `local`（ComfyUI graph，已存在）② `comfy_cloud`（comfy.org 圖＋成本確認，已存在）③ `generic_web`（通用貼上塊：完整 prompt＋上傳 ref 指示＋參數卡＋Avoid 清單，Hailuo 風格排版） |
| 8.3 | Adapter 處理的怪癖 | negative 折疊 vs 獨立欄位、ref 引用語法（`<Picture 1>` vs 上傳圖）、時長語意（grid 格數 vs 秒數上限） |
| 8.4 | 其他平台 | Kling/Veo/Seedance 等 adapter = v2 |

## 9. 對齊保證（Q13）

| # | 決策 | 結論 |
|---|------|------|
| 9.1 | v1 承諾（輸入上下文對齊） | 本地與網頁收到**完全相同輸入**：同一 final prompt 字串、同一 ref、同一參數、同一 `context_hash`；差異可歸因於平台/模型雜訊，而非漏帶上下文 |
| 9.2 | v2 | 輸出視覺比對（CLIP/video similarity）不進 v1（同一平台重跑都不會逐幀一致，結果不可靠） |
| 9.3 | 機制 | clip 記錄 `platform: local\|web` ＋ context_hash；UI 同顆 cut 並排顯示雙平台 metadata；`verify.py` 報過期清單（clip hash ≠ 封包 hash） |

## 10. Cut 生命週期（Q14）

| # | 決策 | 結論 |
|---|------|------|
| 10.1 | 狀態機 | `draft → locked → generating → generated → accepted`；`stale`（任何輸入變更 → hash 失配 → 自動降回 draft 前段）；`failed`（可重試） |
| 10.2 | 推進者 | lock / generate / import-web = scripts 或 UI；**accepted 只有人（使用者）能按** |
| 10.3 | 專案層 | 全部 cuts = accepted ＝「組裝就緒」旗標 |

## 11. 落地與遷移（Q15）

| # | 決策 | 結論 |
|---|------|------|
| 11.1 | 佈局 | `app/`（引擎：PROTOCOL.md、items.schema.json、scripts：plan/build/lock/export/run/verify/assemble_mv、server.py、ui/index.html）；`luna-comic/` 原地保留為 sample project |
| 11.2 | manifest.json | 新增：歌曲/角色/風格/素材/時長/BPM 宣告 |
| 11.3 | items.json | 新增：從現有文字反推（遷移第 1–2 步） |
| 11.4 | shots.json | 增欄：items 引用、continuity_in/out、lyric_intent；beatmap/lyrics 不動；out/ 重建 |
| 11.5 | 遷移 5 步 | ①反推 scene/look/set_piece（facet 逐欄補）②character/style 從 locked_keywords 直搬 ③逐鏡填 continuity＋lyric_intent ④人 review diff → lock → 驗證 26 鏡可編譯出封包 ⑤panels.json（legacy 漫畫軌）保留、manifest 標註 superseded — 遷移本身即「agent 補齊細節」的示範 |

## 12. 明確延後 / 範圍外

| 項目 | 時機 |
|---|---|
| chain-ref 接棒幀 | v2 / opt-in |
| 輸出視覺比對 | v2 |
| Kling / Veo / Seedance adapter | v2 |
| 歌詞驅動嘴型/人聲 | v2 |
| 影片剪輯功能 | **永不進 app**（assemble_mv.py 為唯一剪輯入口） |
| MVP / demo 驗收標準 | **延後** — 本波設計完成後再議 |

---

## 附：決策樹關係（依賴順序）

```
定位/形式(§1) → 工作流邊界(§2) → 資料模型(§3) → 變異規則(§3.5)
                    → 細節契約(§4) → 歌詞耦合(§5)
                    → 動態連續性(§6) → 封包(§7) → 平台(§8) → 對齊保證(§9)
                    → 生命週期(§10) → 落地/遷移(§11)
```