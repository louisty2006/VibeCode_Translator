#!/usr/bin/env python3
"""
VibeCode Translator — Global code explainer
Highlight any code → Cmd+Ctrl+E → natural language explanation
"""

import sys
import os
import threading
import subprocess
import time

# ── Debug logging to file (packaged app has no visible stdout) ─────────────────
_LOG_PATH = os.path.expanduser("~/vibecode_debug.log")
def _log(msg):
    try:
        with open(_LOG_PATH, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass

import AppKit
import objc
from Foundation import NSObject, NSMakeRect
import rumps
import Quartz
from pynput import keyboard as kb

from settings import load_settings, save_settings
from explainer import explain_code
from bubble import show_bubble
from providers import PROVIDERS, PROVIDER_BY_ID, DEFAULT_PROVIDER_ID
from ui_theme import (
    fill_cream_background,
    make_glass_card,
    make_label,
    setup_glass_window,
    style_pill_button,
    style_popup,
    style_text_field,
)

# ── Text editing (menu bar apps lack a standard Edit menu) ─────────────────────

class EditableTextField(AppKit.NSTextField):
    def _is_active_field(self):
        window = self.window()
        if window is None:
            return False
        first_responder = window.firstResponder()
        if first_responder == self:
            return True
        editor = self.currentEditor()
        return editor is not None and first_responder == editor

    def mouseDown_(self, event):
        window = self.window()
        if window is not None:
            window.makeFirstResponder_(self)
        objc.super(EditableTextField, self).mouseDown_(event)

    def performKeyEquivalent_(self, event):
        if not self._is_active_field():
            return objc.super(EditableTextField, self).performKeyEquivalent_(event)
        modifiers = event.modifierFlags() & AppKit.NSDeviceIndependentModifierFlagsMask
        if modifiers != AppKit.NSCommandKeyMask:
            return objc.super(EditableTextField, self).performKeyEquivalent_(event)
        key = event.charactersIgnoringModifiers()
        if key == "v":
            return self._paste_from_clipboard()
        if key == "c":
            return self._copy_to_clipboard()
        if key == "x":
            return self._cut_to_clipboard()
        if key == "a":
            self.selectText_(None)
            return True
        return objc.super(EditableTextField, self).performKeyEquivalent_(event)

    def _paste_from_clipboard(self):
        text = AppKit.NSPasteboard.generalPasteboard().stringForType_(AppKit.NSPasteboardTypeString)
        if not text:
            return True
        text = "".join(text.split())
        editor = self.currentEditor()
        if editor:
            editor.insertText_(text)
        else:
            self.setStringValue_(text)
        return True

    def _copy_to_clipboard(self):
        text = self._selected_or_all_text()
        if not text:
            return True
        pb = AppKit.NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, AppKit.NSPasteboardTypeString)
        return True

    def _cut_to_clipboard(self):
        editor = self.currentEditor()
        if editor:
            selected = editor.selectedRange()
            if selected.length > 0:
                start = selected.location
                text = self.stringValue()[start:start + selected.length]
                pb = AppKit.NSPasteboard.generalPasteboard()
                pb.clearContents()
                pb.setString_forType_(text, AppKit.NSPasteboardTypeString)
                editor.insertText_("")
            return True
        text = self.stringValue()
        if text:
            pb = AppKit.NSPasteboard.generalPasteboard()
            pb.clearContents()
            pb.setString_forType_(text, AppKit.NSPasteboardTypeString)
            self.setStringValue_("")
        return True

    def _selected_or_all_text(self):
        full = self.stringValue()
        editor = self.currentEditor()
        if editor:
            selected = editor.selectedRange()
            if selected.length > 0:
                start = selected.location
                return full[start:start + selected.length]
        return full


def _ensure_edit_menu():
    app = AppKit.NSApplication.sharedApplication()
    if app is None:
        return
    main_menu = app.mainMenu()
    if main_menu is None:
        main_menu = AppKit.NSMenu.alloc().init()
        app.setMainMenu_(main_menu)
    for item in main_menu.itemArray():
        if item.title() == "Edit":
            return
    edit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Edit", None, "")
    edit_menu = AppKit.NSMenu.alloc().initWithTitle_("Edit")
    edit_item.setSubmenu_(edit_menu)
    main_menu.addItem_(edit_item)
    for title, action, key in [("Cut", "cut:", "x"), ("Copy", "copy:", "c"),
                                ("Paste", "paste:", "v"), ("Select All", "selectAll:", "a")]:
        item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, key)
        item.setKeyEquivalentModifierMask_(AppKit.NSCommandKeyMask)
        edit_menu.addItem_(item)

# ── Settings window ────────────────────────────────────────────────────────────

class _SettingsWindowController(NSObject):
    def initWithSettings_(self, settings):
        self = objc.super(_SettingsWindowController, self).init()
        if self is None:
            return None
        self._settings = settings
        self._panel = None
        self._key_field = None
        self._model_field = None
        self._provider_select = None
        self._lang_select = None
        self._provider_ids = [p["id"] for p in PROVIDERS]
        return self

    def show(self):
        _ensure_edit_menu()
        settings = self._settings
        current_provider = settings.get("provider", DEFAULT_PROVIDER_ID)
        current_cfg = PROVIDER_BY_ID.get(current_provider, PROVIDERS[0])

        win_w, win_h = 440, 330
        panel = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, win_w, win_h),
            AppKit.NSWindowStyleMaskTitled | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        panel.setTitle_("VibeCode Translator Settings")
        panel.setDelegate_(self)
        setup_glass_window(panel, win_w, win_h)
        self._panel = panel

        content = AppKit.NSView.alloc().initWithFrame_(NSMakeRect(0, 0, win_w, win_h))
        fill_cream_background(content)
        panel.setContentView_(content)

        title = make_label("✦ VibeCode Translator", size=17.0, bold=True)
        title.setFrame_(NSMakeRect(24, win_h - 40, 300, 22))
        content.addSubview_(title)

        subtitle = make_label("Enter your API Key to get started", size=12.0, secondary=True)
        subtitle.setFrame_(NSMakeRect(24, win_h - 62, 392, 18))
        content.addSubview_(subtitle)

        # Mint card: provider / key / model
        mint_card = make_glass_card(NSMakeRect(20, 118, 400, 148), tint="mint")
        content.addSubview_(mint_card)

        provider_label = make_label("AI Provider:", size=12.0, secondary=True)
        provider_label.setFrame_(NSMakeRect(16, 112, 100, 18))
        mint_card.addSubview_(provider_label)

        provider_select = AppKit.NSPopUpButton.alloc().initWithFrame_(NSMakeRect(120, 109, 264, 26))
        provider_select.addItemsWithTitles_([p["label"] for p in PROVIDERS])
        if current_provider in self._provider_ids:
            provider_select.selectItemAtIndex_(self._provider_ids.index(current_provider))
        style_popup(provider_select)
        mint_card.addSubview_(provider_select)
        self._provider_select = provider_select

        key_label = make_label("API Key:", size=12.0, secondary=True)
        key_label.setFrame_(NSMakeRect(16, 78, 100, 18))
        mint_card.addSubview_(key_label)

        key_field = EditableTextField.alloc().initWithFrame_(NSMakeRect(120, 75, 264, 26))
        key_field.setStringValue_(settings.get("api_key", ""))
        key_field.setPlaceholderString_(current_cfg.get("key_placeholder", "sk-..."))
        style_text_field(key_field)
        mint_card.addSubview_(key_field)
        self._key_field = key_field

        model_label = make_label("Model (optional):", size=12.0, secondary=True)
        model_label.setFrame_(NSMakeRect(16, 44, 120, 18))
        mint_card.addSubview_(model_label)

        model_field = EditableTextField.alloc().initWithFrame_(NSMakeRect(120, 41, 264, 26))
        model_field.setStringValue_(settings.get("model", ""))
        model_field.setPlaceholderString_(current_cfg.get("model", ""))
        style_text_field(model_field)
        mint_card.addSubview_(model_field)
        self._model_field = model_field

        # Peach card: language + shortcut hint
        peach_card = make_glass_card(NSMakeRect(20, 58, 400, 48), tint="peach")
        content.addSubview_(peach_card)

        lang_label = make_label("Explanation Language:", size=12.0, secondary=True)
        lang_label.setFrame_(NSMakeRect(16, 14, 140, 18))
        peach_card.addSubview_(lang_label)

        lang_select = AppKit.NSPopUpButton.alloc().initWithFrame_(NSMakeRect(160, 11, 200, 26))
        lang_select.addItemsWithTitles_(["English", "繁體中文"])
        if settings.get("language", "en") == "zh":
            lang_select.selectItemAtIndex_(1)
        style_popup(lang_select)
        peach_card.addSubview_(lang_select)
        self._lang_select = lang_select

        provider_select.setNextKeyView_(key_field)
        key_field.setNextKeyView_(model_field)
        model_field.setNextKeyView_(lang_select)

        cancel_btn = AppKit.NSButton.alloc().initWithFrame_(NSMakeRect(228, 16, 96, 34))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setKeyEquivalent_("\x1b")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_(objc.selector(self.cancel_, signature=b"v@:@"))
        style_pill_button(cancel_btn, accent=False)
        content.addSubview_(cancel_btn)

        save_btn = AppKit.NSButton.alloc().initWithFrame_(NSMakeRect(334, 16, 86, 34))
        save_btn.setTitle_("Save")
        save_btn.setKeyEquivalent_("\r")
        save_btn.setTarget_(self)
        save_btn.setAction_(objc.selector(self.save_, signature=b"v@:@"))
        style_pill_button(save_btn, accent=True)
        content.addSubview_(save_btn)

        panel.center()
        panel.makeKeyAndOrderFront_(None)
        panel.makeFirstResponder_(key_field)
        AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    def save_(self, sender):
        provider = self._provider_ids[self._provider_select.indexOfSelectedItem()]
        language = "en" if self._lang_select.indexOfSelectedItem() == 0 else "zh"
        save_settings({
            "provider": provider,
            "api_key": "".join(self._key_field.stringValue().split()),
            "model": self._model_field.stringValue().strip(),
            "language": language,
        })
        _clear_settings_controller()
        self._panel.orderOut_(None)

    def cancel_(self, sender):
        _clear_settings_controller()
        self._panel.orderOut_(None)

    def windowShouldClose_(self, sender):
        _clear_settings_controller()
        return True


_settings_controller = None

def _clear_settings_controller():
    global _settings_controller
    _settings_controller = None

def open_settings():
    global _settings_controller
    if _settings_controller is not None:
        _settings_controller._panel.makeKeyAndOrderFront_(None)
        AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        return
    _settings_controller = _SettingsWindowController.alloc().initWithSettings_(load_settings())
    _settings_controller.show()


def has_accessibility_permission():
    from ApplicationServices import AXIsProcessTrusted
    return bool(AXIsProcessTrusted())


def _accessibility_python_hint():
    exe = os.path.realpath(sys.executable)
    app_bundle = os.path.join(os.path.dirname(os.path.dirname(exe)), "Resources", "Python.app")
    return app_bundle if os.path.exists(app_bundle) else sys.executable


def open_accessibility_settings():
    for url in [
        "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
    ]:
        if subprocess.run(["open", url], capture_output=True).returncode == 0:
            return True
    return False


def show_accessibility_prompt(then=None):
    python_path = _accessibility_python_hint()
    alert = AppKit.NSAlert.alloc().init()
    alert.setMessageText_("Enable Accessibility for Cmd+Shift+E")
    alert.setInformativeText_(
        "VibeCode Translator needs Accessibility permission to listen for Cmd+Shift+E.\n\n"
        "1. Click Open System Settings\n"
        "2. Enable Terminal and Python.app (Homebrew)\n"
        f"3. If needed, add:\n{python_path}\n\n"
        "Then quit and restart VibeCode Translator."
    )
    alert.addButtonWithTitle_("Open System Settings")
    alert.addButtonWithTitle_("Later")
    if alert.runModal() == AppKit.NSAlertFirstButtonReturn:
        open_accessibility_settings()
    if then:
        then()

# ── Global hotkey via pynput ───────────────────────────────────────────────────

_pressed_keys = set()
_last_trigger_time = 0.0
_trigger_lock = threading.Lock()

def _hotkey_matched(pressed):
    has_cmd   = any(k in pressed for k in (kb.Key.cmd, kb.Key.cmd_l, kb.Key.cmd_r))
    has_shift = any(k in pressed for k in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r))
    has_e     = any(hasattr(k, 'char') and k.char and k.char.lower() == 'e' for k in pressed)
    return has_cmd and has_shift and has_e

def get_selected_text() -> str:
    src = Quartz.CGEventCreateKeyboardEvent(None, 0x08, True)
    Quartz.CGEventSetFlags(src, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, src)
    src2 = Quartz.CGEventCreateKeyboardEvent(None, 0x08, False)
    Quartz.CGEventSetFlags(src2, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, src2)
    time.sleep(0.15)
    return (AppKit.NSPasteboard.generalPasteboard().stringForType_(AppKit.NSPasteboardTypeString) or "").strip()

def trigger_explain():
    _log("trigger_explain entered")
    if not _trigger_lock.acquire(blocking=False):
        _log("trigger_explain: lock busy, skip")
        return
    try:
        text = get_selected_text()
        _log(f"selected text len={len(text)}")
        if not text:
            show_bubble("⚠️ Please highlight some code first")
            return
        show_bubble("⏳ Analyzing, please wait...")
        result = explain_code(text)
        show_bubble(result)
    except Exception as e:
        show_bubble(f"❌ Error: {e}")
    finally:
        _trigger_lock.release()

def on_press(key):
    _pressed_keys.add(key)
    _log(f"on_press {key!r}")
    if _hotkey_matched(_pressed_keys):
        global _last_trigger_time
        now = time.time()
        if now - _last_trigger_time < 1.5:
            return
        _last_trigger_time = now
        _log("HOTKEY MATCHED -> trigger_explain")
        threading.Thread(target=trigger_explain, daemon=True).start()

def on_release(key):
    _pressed_keys.discard(key)
    if hasattr(key, 'char') and key.char:
        _pressed_keys.discard(key.char.lower())

def start_hotkey_listener():
    _log("start_hotkey_listener called")
    listener = kb.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()
    _log(f"listener started, running={listener.running}")

# ── Menu bar app ───────────────────────────────────────────────────────────────

class VibeCodeTranslatorApp(rumps.App):
    def __init__(self):
        super().__init__("✦", quit_button="Quit VibeCode Translator")
        _ensure_edit_menu()
        self.menu = [
            rumps.MenuItem("⚙️  Settings", callback=lambda _: open_settings()),
            rumps.MenuItem("🔓 Enable Shortcut", callback=self.enable_shortcut),
rumps.MenuItem("📖  Help", callback=self.show_help),
            None,
        ]
        self._startup_timer = rumps.Timer(self._run_startup_flow, 0.5)
        self._startup_timer.start()

    def _run_startup_flow(self, _):
        self._startup_timer.stop()
        if not has_accessibility_permission():
            show_accessibility_prompt(then=self._open_settings_if_needed)
        else:
            self._open_settings_if_needed()

    def _open_settings_if_needed(self):
        if not load_settings().get("api_key"):
            open_settings()

    def enable_shortcut(self, _):
        if has_accessibility_permission():
            show_bubble("✅ Shortcut enabled. Use Cmd + Control + E on highlighted code.")
            return
        show_accessibility_prompt()

    def show_help(self, _):
        show_bubble(
            "How to use VibeCode Translator\n\n"
            "1. Highlight any code\n"
            "2. Press Cmd + Control + E\n"
            "   (requires 🔓 Enable Shortcut first)\n\n"
            "First time? Open ⚙️ Settings and enter your API Key"
        )

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start_hotkey_listener()
    app = VibeCodeTranslatorApp()
    app.run()
