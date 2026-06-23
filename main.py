#!/usr/bin/env python3
"""
VibeCode Translator — Global code explainer
Highlight any code → Cmd+Shift+E or right-click menu → natural language explanation
"""

import sys
import os
import threading
import subprocess
import time

import AppKit
import objc
from Foundation import NSObject, NSMakeRect
import rumps
import Quartz

from settings import load_settings, save_settings
from explainer import explain_code
from bubble import show_bubble, show_loading_bubble
from providers import PROVIDERS, PROVIDER_BY_ID, DEFAULT_PROVIDER_ID

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
        text = AppKit.NSPasteboard.generalPasteboard().stringForType_(
            AppKit.NSPasteboardTypeString
        )
        if not text:
            return True
        # Strip all whitespace/newlines so pasted API keys are clean
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
    """Menu bar apps have no Edit menu; wire standard copy/paste to first responder."""
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

    entries = [
        ("Cut", "cut:", "x"),
        ("Copy", "copy:", "c"),
        ("Paste", "paste:", "v"),
        ("Select All", "selectAll:", "a"),
    ]
    for title, action, key in entries:
        item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            title, action, key
        )
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
        self._modal_done = False
        return self

    def show(self):
        _ensure_edit_menu()
        settings = self._settings
        current_provider = settings.get("provider", DEFAULT_PROVIDER_ID)
        current_cfg = PROVIDER_BY_ID.get(current_provider, PROVIDERS[0])

        panel = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 420, 260),
            AppKit.NSWindowStyleMaskTitled | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        panel.setTitle_("VibeCode Translator Settings")
        panel.setDelegate_(self)
        self._panel = panel

        content = panel.contentView()

        subtitle = AppKit.NSTextField.labelWithString_("Enter your API Key to get started")
        subtitle.setFrame_(NSMakeRect(20, 220, 380, 20))
        subtitle.setTextColor_(AppKit.NSColor.secondaryLabelColor())
        content.addSubview_(subtitle)

        provider_label = AppKit.NSTextField.labelWithString_("AI Provider:")
        provider_label.setFrame_(NSMakeRect(20, 185, 110, 20))
        content.addSubview_(provider_label)

        provider_select = AppKit.NSPopUpButton.alloc().initWithFrame_(NSMakeRect(140, 183, 260, 24))
        provider_select.addItemsWithTitles_([p["label"] for p in PROVIDERS])
        if current_provider in self._provider_ids:
            provider_select.selectItemAtIndex_(self._provider_ids.index(current_provider))
        content.addSubview_(provider_select)
        self._provider_select = provider_select

        key_label = AppKit.NSTextField.labelWithString_("API Key:")
        key_label.setFrame_(NSMakeRect(20, 150, 110, 20))
        content.addSubview_(key_label)

        key_field = EditableTextField.alloc().initWithFrame_(NSMakeRect(140, 148, 260, 24))
        key_field.setStringValue_(settings.get("api_key", ""))
        key_field.setPlaceholderString_(current_cfg.get("key_placeholder", "sk-..."))
        content.addSubview_(key_field)
        self._key_field = key_field

        model_label = AppKit.NSTextField.labelWithString_("Model (optional):")
        model_label.setFrame_(NSMakeRect(20, 115, 120, 20))
        content.addSubview_(model_label)

        model_field = EditableTextField.alloc().initWithFrame_(NSMakeRect(140, 113, 260, 24))
        model_field.setStringValue_(settings.get("model", ""))
        model_field.setPlaceholderString_(current_cfg.get("model", ""))
        content.addSubview_(model_field)
        self._model_field = model_field

        lang_label = AppKit.NSTextField.labelWithString_("Explanation Language:")
        lang_label.setFrame_(NSMakeRect(20, 80, 130, 20))
        content.addSubview_(lang_label)

        lang_select = AppKit.NSPopUpButton.alloc().initWithFrame_(NSMakeRect(160, 78, 160, 24))
        lang_select.addItemsWithTitles_(["English", "繁體中文"])
        if settings.get("language", "en") == "zh":
            lang_select.selectItemAtIndex_(1)
        content.addSubview_(lang_select)
        self._lang_select = lang_select

        provider_select.setNextKeyView_(key_field)
        key_field.setNextKeyView_(model_field)
        model_field.setNextKeyView_(lang_select)

        hint = AppKit.NSTextField.labelWithString_("Shortcut: Cmd + Shift + E")
        hint.setFrame_(NSMakeRect(20, 50, 300, 20))
        hint.setTextColor_(AppKit.NSColor.secondaryLabelColor())
        hint.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
        content.addSubview_(hint)

        save_btn = AppKit.NSButton.alloc().initWithFrame_(NSMakeRect(300, 12, 100, 28))
        save_btn.setTitle_("Save")
        save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        save_btn.setKeyEquivalent_("\r")
        save_btn.setTarget_(self)
        save_btn.setAction_(objc.selector(self.save_, signature=b"v@:@"))
        content.addSubview_(save_btn)

        cancel_btn = AppKit.NSButton.alloc().initWithFrame_(NSMakeRect(190, 12, 100, 28))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        cancel_btn.setKeyEquivalent_("\x1b")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_(objc.selector(self.cancel_, signature=b"v@:@"))
        content.addSubview_(cancel_btn)

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


# Global reference keeps the controller alive while the window is open
_settings_controller = None

def _clear_settings_controller():
    global _settings_controller
    _settings_controller = None

def open_settings():
    global _settings_controller
    if _settings_controller is not None:
        # Already open — bring to front
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
    app_bundle = os.path.join(
        os.path.dirname(os.path.dirname(exe)),
        "Resources",
        "Python.app",
    )
    if os.path.exists(app_bundle):
        return app_bundle
    return sys.executable


def open_accessibility_settings():
    urls = [
        "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
    ]
    for url in urls:
        result = subprocess.run(["open", url], capture_output=True)
        if result.returncode == 0:
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

from pynput import keyboard as kb

_hotkey_combo = {kb.Key.cmd, kb.Key.shift, kb.KeyCode.from_char('e')}
_pressed_keys = set()
_last_trigger_time = 0.0
_trigger_lock = threading.Lock()

def _key_matches_combo(pressed: set) -> bool:
    """Check hotkey ignoring case and cmd_l/cmd_r/shift_l/shift_r variants."""
    has_cmd = any(k in pressed for k in (kb.Key.cmd, kb.Key.cmd_l, kb.Key.cmd_r))
    has_shift = any(k in pressed for k in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r))
    has_e = any(
        (hasattr(k, 'char') and k.char and k.char.lower() == 'e')
        for k in pressed
    )
    return has_cmd and has_shift and has_e

def get_selected_text() -> str:
    """Copy selected text to clipboard and return it."""
    original = AppKit.NSPasteboard.generalPasteboard().stringForType_(
        AppKit.NSPasteboardTypeString
    ) or ""
    # Simulate Cmd+C
    src = Quartz.CGEventCreateKeyboardEvent(None, 0x08, True)   # C key down
    Quartz.CGEventSetFlags(src, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, src)
    src2 = Quartz.CGEventCreateKeyboardEvent(None, 0x08, False)
    Quartz.CGEventSetFlags(src2, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, src2)
    time.sleep(0.15)
    text = AppKit.NSPasteboard.generalPasteboard().stringForType_(
        AppKit.NSPasteboardTypeString
    ) or ""
    return text.strip()

def trigger_explain():
    if not _trigger_lock.acquire(blocking=False):
        return
    try:
        print("[DEBUG] trigger_explain() called", flush=True)
        text = get_selected_text()
        print(f"[DEBUG] selected text: {repr(text[:80]) if text else '(empty)'}", flush=True)
        if not text:
            show_bubble("⚠️ Please highlight some code first")
            return
        show_loading_bubble()
        result = explain_code(text)
        show_bubble(result)
    except Exception as e:
        print(f"[DEBUG] explain error: {e}", flush=True)
        show_bubble(f"❌ Error: {e}")
    finally:
        _trigger_lock.release()

def on_press(key):
    _pressed_keys.add(key)
    if _key_matches_combo(_pressed_keys):
        global _last_trigger_time
        now = time.time()
        if now - _last_trigger_time < 1.5:
            return
        _last_trigger_time = now
        print(f"[DEBUG] Hotkey detected! keys={_pressed_keys}", flush=True)
        threading.Thread(target=trigger_explain, daemon=True).start()

def on_release(key):
    _pressed_keys.discard(key)
    # Also clear any char-equivalent that might have been added under a different representation
    if hasattr(key, 'char') and key.char:
        _pressed_keys.discard(key.char)
        _pressed_keys.discard(key.char.lower())
        _pressed_keys.discard(key.char.upper())

def start_hotkey_listener():
    listener = kb.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()

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
            show_bubble("✅ Shortcut enabled. Use Cmd + Shift + E on highlighted code.")
            return
        show_accessibility_prompt()

    def show_help(self, _):
        show_bubble(
            "How to use VibeCode Translator\n\n"
            "1. Highlight any code\n"
            "2. Press Cmd + Shift + E\n"
            "   (requires 🔓 Enable Shortcut first)\n\n"
            "First time? Open ⚙️ Settings and enter your API Key"
        )

# ── Right-click interception via CGEventTap ────────────────────────────────────

_right_click_pending = False

def setup_right_click_menu():
    """
    Intercept right-click: show a small NSMenu with 'Explain Code' option.
    Falls back gracefully in apps that have their own context menus.
    """
    def event_callback(proxy, event_type, event, refcon):
        global _right_click_pending
        if event_type == Quartz.kCGEventRightMouseDown:
            _right_click_pending = True
        elif event_type == Quartz.kCGEventRightMouseUp and _right_click_pending:
            _right_click_pending = False

            def show_context_menu():
                menu = AppKit.NSMenu.alloc().init()
                item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "✦ Explain Code", None, ""
                )

                class MenuDelegate(NSObject):
                    def menuItemClicked_(self, sender):
                        trigger_explain()

                delegate = MenuDelegate.alloc().init()
                item.setTarget_(delegate)
                item.setAction_(objc.selector(delegate.menuItemClicked_, signature=b'v@:@'))
                menu.addItem_(item)

                loc = AppKit.NSEvent.mouseLocation()
                # NSMenu needs a view to pop from; use a dummy approach
                AppKit.NSMenu.popUpContextMenu_withEvent_forView_(
                    menu,
                    AppKit.NSApp.currentEvent(),
                    AppKit.NSApp.keyWindow().contentView() if AppKit.NSApp.keyWindow() else None
                )

            AppKit.NSApp.performSelectorOnMainThread_withObject_waitUntilDone_(
                objc.selector(show_context_menu, signature=b'v@:'), None, False
            )

        return event

    mask = (
        Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseDown) |
        Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseUp)
    )
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,
        Quartz.kCGHeadInsertEventTap,
        Quartz.kCGEventTapOptionDefault,
        mask,
        event_callback,
        None
    )
    if tap:
        run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(),
            run_loop_source,
            Quartz.kCFRunLoopCommonModes
        )
        Quartz.CGEventTapEnable(tap, True)

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start_hotkey_listener()

    app = VibeCodeTranslatorApp()
    app.run()
