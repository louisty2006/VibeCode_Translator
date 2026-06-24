# VibeCode Translator — Development Log / 開發日誌

## Version History / 版本歷史

| Version | Branch | Key Change / 主要改動 |
|---------|--------|-----------------------|
| MVP1 (1.0) | `main` | CLI hotkey works, plain UI / CLI 快捷鍵可用，純文字介面 |
| MVP2 (2.0.x) | `mvp1-rewrite-glass-ui` | Glass UI, packaged `.app`, hotkey broken / 玻璃 UI，打包 .app，快捷鍵失效 |
| **MVP2.1 (2.1.0)** | `mvp2-carbon-hotkey` | **Packaged app hotkey fixed / 打包 app 快捷鍵修復** |

---

## MVP2.1 — The Packaged App Hotkey Fix / 打包 App 快捷鍵修復

### The Problem / 問題

```
CLI 執行    →  Cmd+Ctrl+E  →  ✅ Bubble 彈出
.app 執行   →  Cmd+Ctrl+E  →  ❌ 完全沒反應
```

Same code. Same machine. Only the packaging broke it.
同一份 code，同一台機器，只有打包後失效。

---

### Full Debug Journey / 完整偵錯歷程

```
┌─────────────────────────────────────────────────────────────────────┐
│  ROOT QUESTION / 核心問題：                                          │
│  Why does the hotkey work in CLI but not in .app?                   │
│  為什麼快捷鍵在 CLI 正常，打包後完全無反應？                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 1 / 嘗試一 — pynput (CGEventTap)                           │
│                                                                     │
│  How it works: pynput taps the global keyboard event stream         │
│  原理：pynput 監聽全域鍵盤事件流                                      │
│  Requires / 需要：Accessibility 權限 (TCC)                           │
│                                                                     │
│  Log showed / Log 顯示：                                             │
│    "listener started, running=True"                                 │
│    → ZERO key events received / 收到 0 個鍵盤事件                    │
│                                                                     │
│  WHY IT FAILED / 為何失敗：                                          │
│  The .app is ad-hoc signed. Every py2app rebuild changes the        │
│  binary hash. macOS TCC stores a hash (csreq) at grant time —      │
│  new hash = new app in TCC's eyes = permission denied.              │
│                                                                     │
│  .app 是 ad-hoc 簽名。每次 rebuild 都換 binary hash。               │
│  macOS TCC 在授權時記錄 hash（csreq）—— 新 hash = 新 app = 拒絕。  │
│                                                                     │
│  ❌ Re-granting permission after each rebuild didn't help either.   │
│  ❌ 每次重新授權也沒用。                                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │ switched API / 換 API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 2 / 嘗試二 — NSEvent.addGlobalMonitorForEventsMatchingMask │
│                                                                     │
│  How it works: Native Cocoa global keyboard monitor                 │
│  原理：原生 Cocoa 全域鍵盤監聽                                        │
│  Requires / 需要：Accessibility 權限 (TCC) — same as pynput / 同上  │
│                                                                     │
│  Bugs fixed along the way / 過程中修復的 bug：                       │
│   • App 死機 (1)：NSAlert.runModal() 阻塞主線程                     │
│   • App 死機 (2)：在 runloop 啟動前就註冊 monitor                   │
│   • Monitor 靜默失效：Python GC 清掉了 handler object               │
│                                                                     │
│  After fixing all freezes, added diagnostic / 修復死機後加入診斷：  │
│    _log(f"accessibility={has_accessibility_permission()}")          │
│                                                                     │
│  Log showed / Log 顯示："accessibility=False"                       │
│                                                                     │
│  💡 KEY INSIGHT / 關鍵轉折：                                         │
│  Both APIs need Accessibility. Ad-hoc signing = it never sticks.   │
│  兩個 API 都需要 Accessibility。Ad-hoc 簽名 = 授權永遠不穩。         │
│  Must find an API that needs NO Accessibility at all.               │
│  必須找一個完全不需要 Accessibility 的 API。                          │
│                                                                     │
│  ❌ Same root cause as Attempt 1 / 根本原因與嘗試一相同。            │
└────────────────────────────┬────────────────────────────────────────┘
                             │ switched API entirely / 根本換掉 API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 3 / 嘗試三 — Carbon RegisterEventHotKey (via ctypes)       │
│                                                                     │
│  How it works: Register a specific key combo with the OS.           │
│  原理：向 OS 登記一個特定按鍵組合。OS 在按下時發送 Carbon 事件。      │
│  Requires / 需要：NOTHING. No Accessibility. No permission.         │
│                  什麼都不需要。免 Accessibility，免權限。             │
│                                                                     │
│  This is how Alfred, Raycast, etc. register global hotkeys.         │
│  Alfred、Raycast 等 app 都是用這個 API 做全域快捷鍵。                │
│                                                                     │
│  ✅ Correct approach — but hit 3 ctypes crashes in a row.           │
│  ✅ 方向正確 — 但連撞三次 ctypes SIGSEGV 閃退。                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CRASH SERIES / 連環閃退 — ctypes 64-bit pointer bugs (ARM64 macOS) │
└─────────────────────────────────────────────────────────────────────┘

  Crash 1 — restype defaults to c_int (32-bit) / restype 預設是 32-bit
  ┌─────────────────────────────────────────────────────────────────┐
  │  GetApplicationEventTarget() returns a 64-bit pointer           │
  │  GetApplicationEventTarget() 回傳 64-bit 指標                   │
  │  ctypes default restype = c_int = 32-bit                        │
  │  High 32 bits silently dropped / 高位 32 bits 被靜默截掉        │
  │                                                                 │
  │  0x60000191d080  →  0x0191d080  (野指標)  →  SIGSEGV           │
  │                                                                 │
  │  Fix / 修法：fn.restype = ctypes.c_void_p                      │
  └─────────────────────────────────────────────────────────────────┘

  Crash 2 — CDLL attribute access creates a new object each time
             CDLL 每次取屬性都產生新 object
  ┌─────────────────────────────────────────────────────────────────┐
  │  _carbon.GetApplicationEventTarget.restype = c_void_p  ← obj A │
  │  target = _carbon.GetApplicationEventTarget()          ← obj B  │
  │                   ^ new object！restype 沒有設到！              │
  │                                                                 │
  │  Same truncation, same crash / 同樣截斷，同樣閃退               │
  │                                                                 │
  │  Fix / 修法：先把 function 存進變數，再設 restype，再 call      │
  │         _get_target = _carbon.GetApplicationEventTarget         │
  │         _get_target.restype = ctypes.c_void_p                   │
  │         target = _get_target()                                  │
  └─────────────────────────────────────────────────────────────────┘

  Crash 3 — Python int passed without argtypes = c_int (32-bit)
             沒設 argtypes，Python int 被當 c_int（32-bit）傳
  ┌─────────────────────────────────────────────────────────────────┐
  │  _get_target() returns a Python int (correct 64-bit value)      │
  │  _get_target() 回傳正確的 64-bit Python int                     │
  │  Passing it to another ctypes call WITHOUT argtypes             │
  │  傳給另一個 ctypes function 但沒設 argtypes                     │
  │  → ctypes treats it as C int = 32-bit → truncated again!        │
  │  → ctypes 視為 C int = 32-bit → 再次截斷！                     │
  │                                                                 │
  │  Confirmed via crash register dump / 靠崩潰報告暫存器確認：     │
  │    x0 = 0x191d080  (low 32 bits of 0x60000191d080)             │
  │         （0x60000191d080 的低 32 bits）                         │
  │                                                                 │
  │  Fix / 修法：包進 ctypes.c_void_p() 再傳                       │
  │         target = ctypes.c_void_p(_get_target())                 │
  └─────────────────────────────────────────────────────────────────┘

                             │  all crashes fixed / 所有閃退修復
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Hotkey fires! But wrong text / 快捷鍵觸發了！但翻譯了錯誤的文字     │
│                                                                     │
│  Problem / 問題：                                                   │
│  get_selected_text() simulates Cmd+C via CGEventPost.              │
│  CGEventPost to HID event tap ALSO needs Accessibility.            │
│  Without it → Cmd+C silently fails → reads stale clipboard.        │
│                                                                     │
│  get_selected_text() 用 CGEventPost 模擬 Cmd+C。                   │
│  CGEventPost 也需要 Accessibility。                                  │
│  沒有 → Cmd+C 靜默失敗 → 讀到的是舊的 clipboard 內容。             │
│                                                                     │
│  Fix / 修法：                                                       │
│  Check AXIsProcessTrusted() before capturing text.                 │
│  先檢查 AXIsProcessTrusted()，缺權限就彈提示 + 開系統設定。         │
│  User grants once. Cmd+C then works permanently.                   │
│  用戶授權一次，之後永遠有效（非 ad-hoc 限制，此權限真正穩定）。      │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
              ✅ FULLY WORKING / 完全正常運作


---

### Two-Permission Model / 雙權限架構（最終設計）

```
User presses / 用戶按下  Cmd+Ctrl+E
                  │
                  ▼
  Carbon RegisterEventHotKey          ← No permission / 免權限
  fires _on_hotkey()
                  │
                  ▼
  Check AXIsProcessTrusted()
                  │
          ┌───────┴───────┐
          │               │
        False           True
          │               │
          ▼               ▼
   彈出提示          CGEventPost Cmd+C   ← Needs Accessibility (once)
   + 自動打開        讀取 clipboard           需 Accessibility（一次）
   系統設定          呼叫 LLM
                    彈出 bubble
```

Hotkey detection never needs permission.
Text capture needs Accessibility once — and the app guides you through it automatically.

快捷鍵偵測永遠不需要權限。
文字擷取需要 Accessibility 一次，app 會自動引導你完成。

---

### What Changes in 2.1.0 / 2.1.0 的改動

**Removed / 移除：**
- `pynput` — replaced by Carbon / 被 Carbon 取代
- `NSEvent.addGlobalMonitorForEventsMatchingMask` — same TCC problem / 同樣 TCC 問題
- `NSAlert.runModal()` startup prompt — blocked main thread / 阻塞主線程
- `show_accessibility_prompt()`, `_run_startup_flow()`, `_startup_timer` — dead code / 死碼
- `_pressed_keys`, `on_press`, `on_release`, `_hotkey_matched` — pynput handlers / pynput 處理器
- Top-level `sys`, `subprocess` imports — no longer needed / 不再需要

**Added / 新增：**
- `Carbon.RegisterEventHotKey` via `ctypes` — permission-free hotkey / 免權限快捷鍵偵測
- `Carbon.InstallEventHandler` via `ctypes` — routes Carbon event to Python / 路由 Carbon 事件到 Python
- `_has_accessibility()` check inside `trigger_explain()` — guides user on first run / 首次使用引導
- `_open_accessibility_settings()` — auto-opens System Settings / 自動打開系統設定

**Fixed / 修復：**
- App frozen on startup (3 separate causes) / App 啟動死機（三個不同原因）
- Global monitor receiving zero events / 全域監聽收不到任何事件
- 3× SIGSEGV from ctypes 64-bit pointer truncation on ARM64 / 三次 ctypes 64-bit 指標截斷閃退

---

### How to Diagnose Future Issues / 如何診斷未來問題

Log file / 日誌文件：`~/vibecode_debug.log`

| Log line / 日誌行 | Meaning / 含義 |
|-------------------|---------------|
| `start_hotkey_listener called` | App 啟動，正在註冊快捷鍵 |
| `EventTarget=0x600...` | 64-bit 指標正常（若數值很小 → 截斷 bug）|
| `RegisterEventHotKey status=0` | 快捷鍵已向 OS 登記 |
| `InstallEventHandler status=0` | Carbon 事件處理器已安裝 |
| `HOTKEY MATCHED -> trigger_explain` | 按鍵組合偵測成功 |
| `accessibility=False` | 未授予 Accessibility（文字擷取會失敗）|
| `selected text len=N` | 從 clipboard 擷取到 N 個字符 |
