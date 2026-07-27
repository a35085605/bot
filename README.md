# bot

一個正在重構中的自動化 Bot 核心架構。

這個專案的目標不是只做出一支依賴固定圖片、座標與流程的腳本，而是建立一套能夠逐步擴充、替換感知技術，並讓決策邏輯保持穩定的 automation bot framework。

> 專案目前處於架構重構與基礎模組建設階段，尚未是一個可直接執行的完整遊戲 Bot。

## 專案在做什麼

Automation bot 通常需要完成一個持續循環：

```text
擷取畫面
    ↓
理解目前畫面與狀態
    ↓
決定下一步行為
    ↓
規劃並執行滑鼠／鍵盤操作
    ↓
重新觀察結果
```

本專案將這個循環拆成彼此邊界清楚的模組：

```text
Capture
    ↓
Vision primitives
    ↓
Perception interpretation
    ↓
World model
    ↓
Decision
    ↓
Planning / Execution
```

目前主要集中在 vision、template assets、template matching 與 world model 的基礎設計。

## 核心目標

### 1. Decision 不依賴特定 perception 技術

Decision 應該只理解語意狀態，例如：

- 目前位於主選單
- Loading indicator 正在顯示
- Confirm control 可見且可操作
- 畫面狀態不確定，需要重新觀察

Decision 不應知道：

- 使用了哪一張 template
- OpenCV matching method
- template matching score
- image hash distance
- OCR engine
- validity mask 或 NMS 設定

這讓 perception 可以在不改動 decision 的情況下替換或組合：

- Template matching
- Image hashing
- OCR
- Color / feature detection
- Object detection
- Accessibility API

### 2. 將 detector result 轉成穩定的世界語意

單次 detector 輸出不等於真實世界狀態。

例如「這一幀沒有找到按鈕」可能代表：

- 按鈕真的不存在
- 畫面模糊
- ROI 被遮住
- detector 暫時漏判
- 截圖已過期

因此 world model 明確區分：

```text
PRESENT
ABSENT
UNKNOWN
```

並透過跨幀追蹤與 scene hysteresis，避免單幀雜訊直接改變 decision 所看到的穩定狀態。

### 3. 建立可替換、可測試的 Vision primitives

Template matching 應只負責：

- 在灰階影像中搜尋模板
- 產生位置與正規化分數
- 收集候選
- 驗證候選
- 使用 NMS 去除重複位置

它不負責：

- 判斷目前是哪一個遊戲頁面
- 決定是否點擊
- 決定 loading 要等待多久
- 決定失敗時如何恢復

相同原則也會套用到 image hashing、OCR 與後續 detector。

### 4. 保護空間資訊與時間資訊

自動化操作不只需要知道「看到什麼」，還需要知道：

- observation 屬於哪一幀
- 畫面何時擷取
- 來自哪一個視窗或裝置
- 座標屬於哪一個 coordinate space
- observation 是否仍然新鮮

World model 因此將 semantic observation 綁定 frame identity、capture time、source 與 root coordinates，避免 decision 或 executor 使用過期位置。

## 架構方向

```text
                        ┌─ template_matching
                        ├─ image_hashing
Capture → Perception ───┼─ OCR
                        └─ other detectors
              │
              ▼
         WorldSnapshot
              │
              ▼
          WorldState
              │
              ▼
           Decision
              │
              ▼
      Intent / Action plan
              │
              ▼
          Execution
```

Dependency 的方向預期如下：

```text
world_model
    不依賴 perception、decision 或 OpenCV

perception
    依賴 world_model
    可依賴 template_matching、image_hashing 等 detector

decision
    只依賴 world_model 的唯讀語意介面
    不依賴任何 detector

application
    負責組裝 capture、perception、decision 與 execution
```

## 目前模組

### `geometry`

提供不可變的幾何 value objects，例如使用 half-open coordinates 的 `Rect`，以及 intersection、containment、IoU 等操作。

### `template_assets`

管理可重用的模板資產：

- Stable template key
- Immutable grayscale pixels
- Binary validity mask
- File / HTTP / package locators
- Manifest 與 provenance
- SHA-256 content verification
- Provider、reader 與 decoder ports

儲存位置與 matching policy 不會被放進 runtime `Template`。

### `template_matching`

提供 detector-level template matching：

- OpenCV adapter
- 統一為 `[0, 1]` 且越高越好的 score contract
- 多候選收集
- Candidate validation
- Greedy IoU NMS
- Candidate collection floor
- Optional threshold evaluation

長期方向是讓 `match()` 保持為純 vision primitive，並由 perception adapter 將 matching results 轉成 semantic observations。

### `world_model`

定義 perception 與 decision 之間的中立語意模型：

- Strongly typed semantic keys
- `PRESENT / ABSENT / UNKNOWN`
- Frame identity 與 capture metadata
- Scene hypotheses
- Control、indicator 與 value observations
- Immutable `WorldSnapshot`
- Cross-frame `WorldStateTracker`
- Scene confirmation 與 transition detection
- Decision-facing read-only protocol

World model 不暴露 template key、OpenCV score、hash distance 或其他 detector-specific 資訊。

## 目標資料流

```python
frame = capture_service.capture()

snapshot = perception_service.observe(frame)

world_state = world_tracker.update(snapshot)

intents = decision_service.decide(
    world=world_state,
    memory=bot_memory,
)

commands = action_planner.plan(
    intents=intents,
    world=world_state,
)

executor.execute(commands)
```

Decision 預期輸出 semantic intent：

```python
ActivateControl(ControlKey("confirm"))
```

而不是直接輸出：

```python
Click(x=123, y=456)
```

實際座標應由 action planner 使用最新 world state 解析，並在執行前重新檢查 observation freshness。

## 設計原則

- Domain model 優先使用 immutable value objects
- External engine 必須受到 application/domain contract 驗證
- Detector failure 不可偽裝成「確定不存在」
- Candidate collection 與 business acceptance 必須分開
- Runtime asset 不持有 replaceable storage details
- Decision 不 import perception implementation
- Decision intent 不長期保存像素座標
- 執行 action 前必須驗證 observation 是否過期
- 跨幀狀態更新必須 deterministic 且可測試

## 目前進度

已完成或已有基礎實作：

- Geometry rectangle model
- Template asset extraction
- Immutable template pixels and validity masks
- Manifest resolver and digest verification
- OpenCV template matching adapter
- Normalized score contract
- Multi-candidate result model
- IoU non-maximum suppression
- Semantic world model
- Frame freshness and source invariants
- Cross-frame scene stabilization

尚待實作：

- Capture abstraction 與實際 screenshot adapters
- Image hashing module
- OCR / other detectors
- Detector evidence models
- Template matching → world observation adapter
- Multi-detector evidence interpretation / fusion
- Game-specific semantic vocabulary
- Decision policies and bot memory
- Semantic intent and action planner
- Mouse / keyboard execution adapters
- End-to-end automation loop

## 執行測試

```bash
python -m unittest discover -s tests -v
```

檢查 Python modules 是否可編譯：

```bash
python -m compileall -q .
```

## 專案狀態

這個 repository 目前主要用於從舊版 `Game_Bot` codebase 中提取概念、修正模組邊界，並逐步建立新的核心架構。

短期目標是完成：

```text
template matching + image hash
            ↓
semantic perception
            ↓
world model
            ↓
detector-independent decision
```

長期目標則是建立一套可支援不同遊戲、應用程式或裝置的 automation bot foundation，而不是只服務單一固定流程。
