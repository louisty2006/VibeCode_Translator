# VibeCode Translator — Development Log

## Version History

| Version | Branch | Key Change |
|---------|--------|------------|
| MVP1 (1.0) | `main` | CLI hotkey works, plain UI |
| MVP2 (2.0.x) | `mvp1-rewrite-glass-ui` | Glass UI, packaged `.app`, hotkey broken |
| **MVP2.1 (2.1.0)** | `mvp2-carbon-hotkey` | **Packaged app hotkey fixed** |

---

## MVP2.1 — The Packaged App Hotkey Fix

### The Problem

```
CLI run  →  Cmd+Ctrl+E  →  ✅ Bubble appears
.app run →  Cmd+Ctrl+E  →  ❌ Nothing happens
```

Same code. Same machine. Only the packaging broke it.

---

### Full Debug Journey

```
┌─────────────────────────────────────────────────────────────────────┐
│  ROOT QUESTION: Why does the hotkey work in CLI but not in .app?    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 1 — pynput (CGEventTap)                                    │
│                                                                     │
│  How it works:  pynput taps into the global keyboard event stream   │
│  Requires:      Accessibility permission (TCC)                      │
│                                                                     │
│  Log showed:  "listener started, running=True"                      │
│               → ZERO key events received after that                 │
│                                                                     │
│  WHY IT FAILED:                                                     │
│  The .app is ad-hoc signed. Every py2app rebuild changes the        │
│  binary hash. macOS TCC stores a hash (csreq) at grant time —      │
│  new hash = TCC treats it as a different app = permission denied.   │
│                                                                     │
│  ❌ Re-granting permission after each rebuild didn't help either.   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ switched API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 2 — NSEvent.addGlobalMonitorForEventsMatchingMask          │
│                                                                     │
│  How it works:  Native Cocoa global keyboard monitor                │
│  Requires:      Accessibility permission (TCC) — same as pynput     │
│                                                                     │
│  Introduced new bugs along the way (all fixed):                     │
│   • App froze on startup   → NSAlert.runModal() blocked main thread │
│   • App froze again        → registered monitor before runloop      │
│   • Monitor silently died  → Python GC destroyed the handler object │
│                                                                     │
│  After fixing all freeze bugs, added diagnostic:                    │
│    _log(f"accessibility={has_accessibility_permission()}")          │
│                                                                     │
│  Log showed:  "accessibility=False"                                 │
│                                                                     │
│  💡 KEY INSIGHT: Both APIs need Accessibility.                      │
│     Ad-hoc signing = Accessibility never sticks.                    │
│     Must find an API that doesn't need Accessibility at all.        │
│                                                                     │
│  ❌ Same root cause as Attempt 1.                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ switched API entirely
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 3 — Carbon RegisterEventHotKey (via ctypes)                │
│                                                                     │
│  How it works:  Registers a specific key combo with the OS.         │
│                 OS dispatches a Carbon event when combo is pressed. │
│  Requires:      NOTHING. No Accessibility. No special permission.   │
│                                                                     │
│  This is how Alfred, Raycast, etc. register global hotkeys.         │
│                                                                     │
│  ✅ Correct approach — but hit 3 ctypes crashes in a row.           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CRASH SERIES — ctypes 64-bit pointer bugs (ARM64 macOS)            │
└─────────────────────────────────────────────────────────────────────┘

  Crash 1 — restype defaults to c_int (32-bit)
  ┌─────────────────────────────────────────────────────────────────┐
  │  GetApplicationEventTarget() returns a 64-bit pointer           │
  │  ctypes default restype = c_int = 32-bit                        │
  │  High 32 bits silently dropped                                  │
  │                                                                 │
  │  0x60000191d080  →  0x0191d080  (garbage pointer)  →  SIGSEGV  │
  │                                                                 │
  │  Fix: fn.restype = ctypes.c_void_p                              │
  └─────────────────────────────────────────────────────────────────┘

  Crash 2 — CDLL attribute access creates a new object each time
  ┌─────────────────────────────────────────────────────────────────┐
  │  _carbon.GetApplicationEventTarget.restype = c_void_p  ← obj A │
  │  target = _carbon.GetApplicationEventTarget()          ← obj B  │
  │                   ^ new object, restype not set!                │
  │                                                                 │
  │  Same truncation, same crash.                                   │
  │                                                                 │
  │  Fix: save function to a variable first, then set restype,      │
  │       then call — all on the same object.                       │
  │         _get_target = _carbon.GetApplicationEventTarget         │
  │         _get_target.restype = ctypes.c_void_p                   │
  │         target = _get_target()                                  │
  └─────────────────────────────────────────────────────────────────┘

  Crash 3 — Python int passed without argtypes = c_int (32-bit)
  ┌─────────────────────────────────────────────────────────────────┐
  │  _get_target() returns a Python int (correct 64-bit value)      │
  │  Passing Python int to another ctypes call WITHOUT argtypes     │
  │  → ctypes treats it as C int = 32-bit → truncated again!        │
  │                                                                 │
  │  Confirmed via crash register dump:                             │
  │    x0 = 0x191d080  (low 32 bits of 0x60000191d080)             │
  │                                                                 │
  │  Fix: wrap the pointer in ctypes.c_void_p() before passing.    │
  │         target = ctypes.c_void_p(_get_target())                 │
  └─────────────────────────────────────────────────────────────────┘

                             │  all crashes fixed
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Hotkey fires! But wrong text was explained.                        │
│                                                                     │
│  Problem: get_selected_text() simulates Cmd+C via CGEventPost.     │
│  CGEventPost to HID event tap ALSO needs Accessibility.            │
│  Without it → Cmd+C silently fails → reads stale clipboard.        │
│                                                                     │
│  Fix: check AXIsProcessTrusted() before capturing text.            │
│  If missing → show bubble with instructions + open System Settings. │
│  User grants once. Cmd+C then works permanently.                   │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ✅ FULLY WORKING


---

### Two-Permission Model (Final Architecture)

```
User presses Cmd+Ctrl+E
         │
         ▼
  Carbon RegisterEventHotKey          ← No permission needed
  fires _on_hotkey()
         │
         ▼
  Check AXIsProcessTrusted()
         │
    ┌────┴────┐
    │         │
   False     True
    │         │
    ▼         ▼
  Show      CGEventPost Cmd+C         ← Needs Accessibility (once)
  prompt    read clipboard
  + open    call LLM
  settings  show bubble
```

The hotkey always fires. The text capture needs Accessibility, but only once — and the app now guides you through granting it automatically.

---

### What Changes in 2.1.0

**Removed:**
- `pynput` — replaced by Carbon (no Accessibility needed)
- `NSEvent.addGlobalMonitorForEventsMatchingMask` — same TCC problem as pynput
- Startup accessibility alert (`NSAlert.runModal`) — was blocking the main thread
- `show_accessibility_prompt()`, `_run_startup_flow()`, `_startup_timer` — all dead code
- `_pressed_keys`, `on_press`, `on_release`, `_hotkey_matched` — pynput handlers
- `sys` import, `subprocess` import (top-level) — no longer needed

**Added:**
- `Carbon.RegisterEventHotKey` via `ctypes` — permission-free hotkey detection
- `Carbon.InstallEventHandler` via `ctypes` — routes the Carbon event to Python
- Accessibility check inside `trigger_explain()` — guides user on first run
- `_open_accessibility_settings()` — auto-opens System Settings if needed

**Fixed:**
- App frozen on startup (multiple causes, all resolved)
- Global monitor receiving zero events (wrong API, wrong TCC identity)
- 3× SIGSEGV from ctypes 64-bit pointer truncation on ARM64

---

### How to Diagnose Future Issues

Log file: `~/vibecode_debug.log`

| Log line | Meaning |
|----------|---------|
| `start_hotkey_listener called` | App started, registering hotkey |
| `EventTarget=0x600...` | 64-bit pointer OK (if small value → truncation bug) |
| `RegisterEventHotKey status=0` | Hotkey registered with OS |
| `InstallEventHandler status=0` | Carbon event handler installed |
| `HOTKEY MATCHED -> trigger_explain` | Key combo detected |
| `accessibility=False` | Accessibility not granted (text capture will fail) |
| `selected text len=N` | N chars captured from clipboard |
