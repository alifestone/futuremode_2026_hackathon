# PROTOCOL — 影片製作 AI workflow app（agent 面向協議）

> 本文件是「任意 coding agent 驅動本 app」的說明書。agents 照這個文件跑：
> scripts 只做決定性的事；語意判斷（細節完不完整、歌詞意象對不對）由 agent 的
> LLM lint ＋人類 diff review 負責。決策紀錄見 `../decisions.md`。

## 0. 一句話

把「分鏡 → 場景/item 規劃 → 編譯 → 封包 → 執行/匯出」變成有契約、有快照、
本地與網頁拿到**同一份上下文**的管線。角色與場景都被 `items.json` 鎖住，改一處、
所有引用它的鏡頭一起變，hash 會告訴你哪些 clip 過期。

## 1. 檔案地圖

```
app/
├── items.schema.json      # 契約：7 型別＋facets 檢查表＋compile order
├── scripts/
│   ├── build.py           # 決定性渲染引擎 → out/compiled.json（含 context_hash）
│   ├── plan.py            # gap report：agent 的補齊工作條
│   ├── lock.py            # 硬門檻＋凍結封包 → out/packages/<cut>/
│   ├── export.py          # 平台 render：local / comfy_cloud / generic_web
│   ├── run.py             # 本機執行（ComfyUI MiniMax H3）＋ web 結果匯入
│   ├── verify.py          # hash 審計：clip ↔ 封包對帳
│   └── assemble.py        # 剪輯組裝（唯一剪輯入口，app 不做剪輯）
├── server.py              # stdlib HTTP —— Web UI 的薄殼（呼叫上述 scripts）
└── ui/index.html          # 單頁操作面（vanilla JS）
luna-comic/                # sample project：manifest.json / items.json / storyboard/
```

## 2. 契約（agent 必須遵守）

### 2.1 七型別與 compile order（不可更改）
`character → state → scene → set_piece → look → action/camera/sync → style`
- `character` / `style`：全鏡必掛，雷打不動
- `scene` / `look`：每段必掛（缺了 compile 會擋）
- `state`：**事實改變才新建 item**（有觸發時間點），不許寫進 shot 欄位
- `set_piece`：道具一物一 item；不可併入 scene 文字
- `camera_grammar`：可選，一條規則一個 item

### 2.2 修補細節的紀律
- **事實改了 → 新 item 進 items.json**（世界事實只有一份）
- **強調/追加 → shot.overrides[item_id] = 文字**（append-only，永不 replace 基底）
- 有 `lyric_lines` 的鏡頭 **必須**有 `lyric_intent`（歌詞↔畫面耦合）
- 每鏡必須有 `continuity_in` / `continuity_out`（動態連續性鉤子）

### 2.3 兩段式門檻
- `build.py --draft`：缺細節只報 problems，不擋
- `lock.py`：硬門檻 — 引用斷裂、缺 character/scene item、缺 lyric_intent/continuity → 拒絕出封包

## 3. 工作流

### 3.1 遷移新專案（一次性）
建 `manifest.json`（歌曲/角色/風格/素材）→ 從既有素材反推 `items.json`
（照 facets 檢查表逐欄補）→ 逐鏡補 `items` 引用、`continuity_in/out`、
`lyric_intent` → `build.py --draft` 驗證 → 人類 review diff → 進 3.2。

### 3.2 日常編輯迴圈
```
1. 改 storyboard/shots.json（動作/鏡位/表情/continuity/lyric_intent/overrides）
   或 items.json（世界定義）
2. python app/scripts/build.py --draft     # 看 problems + 哪些 cut hash 變了
3. python app/scripts/plan.py              # gap report（缺什麼一目了然）
4. agent 依照 2.2 補齊 → 人類 review diff → 重跑 2-3 直到全綠
5. python app/scripts/lock.py [--cuts S01,...]   # 硬門檻＋凍結封包
```

### 3.3 執行與匯出
```
# 本機（免費，open weights on the box）
python app/scripts/run.py --project luna-comic --cuts S12     # 先產定裝鏡
python app/scripts/run.py --pending                            # 其餘

# 網頁（算力不足時）—— 封包與本機同源、同 hash
python app/scripts/export.py --cut S12 --platform generic_web  # 貼上塊
# 人：複製 prompt、下載 ref、貼到網頁平台生成，下載 clip 後：
python app/scripts/run.py --import-web S12 --file path/S12.mp4

# 對帳＋組裝
python app/scripts/verify.py            # 哪些 clip stale / 缺
python app/scripts/assemble.py --subs   # 唯一剪輯入口 → out/LUNA_MV.mp4
```

## 4. Agent 補齊細節的操作指引（plan pass）

執行 `plan.py --json` 後，對每個缺口：

1. **缺 item / 缺引用**：決定「事實」還是「強調」→ 前者新建 item（id 用
   `scene.`/`set.`/`look.`/`state.`/`cam.` 前綴），後者改 shot overrides。
2. **`lyric_intent` 空**：讀該鏡 `lyric_lines` 對應的歌詞原文（lyrics/lyrics.json），
   寫白話英文「這顆鏡頭怎麼演繹這句歌詞的意象」，不要只複述歌詞。
3. **`continuity_in/out` 空**：讀前後鏡頭 action，推「這顆從哪個姿勢/視線/方向進場、
   以什麼離場」。首鏡 in 寫「frame switching on」，末鏡 out 寫「handing off」。
4. **facets 未覆蓋**：對照 items.schema.json 的檢查表逐項補進 item 文字
   （scene 要有 空間/尺度/時段/天氣/色彩基調；look 要有 主光方向/光質/色溫/氛圍/對比；
   set_piece 要有 位置/尺寸/材質/光照反應/互動；state 要有 觸發時間點）。
5. **語意 lint**：檢查 action 與 lyric_intent 是否同源（例：L04「一張空白的畫面等著
   第一束光出現」的鏡頭必須有「空/光」的視覺對應）；檢查 overrides 沒推翻基底事實。

改完一律重跑 `build.py --draft`，並把「我改了什麼、為何」寫進 commit message，
交人類 review diff。

## 5. 語意（別搞錯）

- **context_hash**：綁定 最終 prompt＋env 無關設定＋ref hash。本地與網頁同 cut 必須
  同 hash。任何輸入變更 → hash 變 → 既有 clip 標 stale（verify.py 報出）。
- **封包 = 凍結快照**：`out/packages/<cut>/context.json` 是匯出當下的上下文副本；
  之後改 items.json 不會污染已匯出封包，只會讓下一次 lock 重算 hash。
- **accepted 只有人**：scripts/UI 都不會替人按「接受」。clip 審查（輸出視覺比對）是 v2，
  v1 只有輸入上下文對齊保證。

## 6. 除錯速查

| 現象 | 原因 | 動作 |
|---|---|---|
| `lock` 擋某 cut | 契約缺欄/引用斷裂 | 看錯誤訊息 → 照 §4 補 |
| build 報 changed 很多 | 你改了 item（鎖連鎖） | 預期行為；確認後全部重生成 |
| verify 報 stale | 生成後上下文變了 | 重 lock → 重生成該 cut |
| run 說 not locked | 沒跑 lock | `lock.py --cuts X` |
| ComfyUI 連不上 | URL 錯/服務沒開 | `COMFYUI_API_URL` 或 `--url` |