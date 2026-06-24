# VibeCode Translator — Handoff Notes

## TL;DR of the open problem

**The global hotkey (`Cmd+Shift+E`) works perfectly when running from source in the
terminal, but does NOT work in the packaged `.app`.** Everything else in the packaged
app works (menu bar icon, Settings window, the explanation bubble — confirmed by
clicking **✦ → Help**, which shows a bubble fine).

### Proof from logging
A file logger writes to `~/vibecode_debug.log` (see `_log()` in `main.py`). Running the
**packaged app** and pressing keys produces only:

```
15:23:32 start_hotkey_listener called
15:23:32 listener started, running=True
```

➡️ The `pynput` keyboard listener **starts successfully but receives ZERO key events**
in the bundle. From the terminal, the same code logs an `on_press` line for every key.

### Diagnosis
This is a macOS **Accessibility (TCC) permission** problem specific to the packaged,
ad-hoc-signed bundle — not a code bug. `pynput`'s macOS backend uses a `CGEventTap`
which silently receives no events unless the *exact running binary* is trusted in
**System Settings → Privacy & Security → Accessibility**.

Key complication: the app is **ad-hoc signed** (`codesign` shows `flags=0x2(adhoc)`).
Every `py2app` rebuild changes the code hash, so macOS treats it as a *new* binary and
**invalidates the previously-granted Accessibility permission**. Re-granting after each
rebuild is required and even then it has not started receiving events.

### What was already tried (all unsuccessful for the packaged app)
- Granted Accessibility to the `.app`, toggled ON, fully quit + relaunched.
- `tccutil reset Accessibility com.vibecode.translator` then re-added fresh.
- Removed stale `Python` / old `VibeCode Translator` entries from the list.
- Confirmed bubble display itself works in the bundle (Help menu).

### Suggested next steps for whoever picks this up
1. **Stable code signing.** Sign the app with a persistent Developer ID (or at least a
   stable self-signed identity) so the TCC grant survives rebuilds:
   `codesign --force --deep --sign "Developer ID Application: …" "dist/VibeCode Translator.app"`.
   Ad-hoc signing is the prime suspect for the permission never sticking.
2. **Verify the bundle identity TCC sees.** After launching the packaged app, check
   Console.app / `log stream --predicate 'subsystem == "com.apple.TCC"'` while pressing
   the hotkey to see what binary is being denied.
3. **Consider an alternative to a global pynput tap.** A native Carbon/Cocoa global
   hotkey (`NSEvent.addGlobalMonitorForEventsMatchingMask:` or `RegisterEventHotKey`)
   integrates better with the app's own run loop and TCC identity than `pynput`'s
   separate event tap.
4. Add `NSAppleEventsUsageDescription` / proper entitlements to the bundle plist.

### Debug logging note
`main.py` currently writes to `~/vibecode_debug.log` on **every keystroke system-wide**
via `_log()` in `on_press`. This is intentional for this diagnosis but should be
**removed before any real release** (performance + privacy). Search for `_log(` to strip it.

---

## MVP1 vs MVP2 (current) — what changed

| Aspect | MVP1 (commit `6972a67`) | MVP2 / current |
|---|---|---|
| **Hotkey** | `Cmd+Shift+E`, hardcoded inline in `main.py` (~10 lines) | Was made customizable via a separate `hotkey.py` (parse/format/record) + a "Record Shortcut" UI. **Now reverted** to hardcoded inline matching; `hotkey.py` deleted. |
| **Trigger lock** | `_trigger_lock.acquire(blocking=False)` — skip if busy | Had a regression: `acquire(timeout=30)` which could block the hotkey for 30s if the lock got stuck. **Now reverted** to `blocking=False`. |
| **UI** | Plain AppKit settings window, dark bubble | **Glassmorphism** UI (`ui_theme.py`): cream gradient, mint/peach glass cards, pill buttons. Bubble restyled to glass. Kept. |
| **Settings window** | provider / key / model / language | Added customizable-hotkey recorder (now removed); back to provider / key / model / language only. |
| **Right-click menu** | `setup_right_click_menu()` (CGEventTap) defined but **never called** (dead code) | Dead code **removed**. |
| **`requests` dep** | listed in requirements | unused, **removed**. |
| **Extra files** | — | `close_bubble()` / `show_loading_bubble()` / `_run_on_main()` dead helpers **removed**. |
| **Packaging** | source only | `py2app` build (`setup.py`, `build_app.sh`) → standalone `.app`. |

### Net of the recent rewrite
The current code is **MVP1's simple, working hotkey logic + MVP2's glassmorphism UI**,
with all the dead code and the customizable-hotkey layer stripped out. The *only*
unresolved issue is the **packaged-app Accessibility/hotkey** problem above.

---

## How to run / build

```bash
# Run from source (this WORKS — hotkey fires):
cd "VibeCode Translator"
./venv311/bin/python main.py      # or: bash run.sh

# Build the .app (hotkey currently does NOT fire in this build):
bash build_app.sh                 # output: dist/VibeCode Translator.app
```

## File map
- `main.py` — menu bar app, settings window, global hotkey listener, trigger flow
- `bubble.py` — floating glass explanation bubble
- `explainer.py` — builds prompt, calls the selected LLM provider
- `providers.py` — registry of 12 AI providers (Claude, GPT, Gemini, Ollama, …)
- `settings.py` — JSON settings at `~/.vibecode_translator_settings.json`
- `ui_theme.py` — glassmorphism styling helpers
- `setup.py` / `build_app.sh` — py2app packaging
