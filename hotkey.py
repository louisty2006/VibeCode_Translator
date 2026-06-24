"""Parse, display, and match global hotkey shortcuts."""

from pynput import keyboard as kb

DEFAULT_HOTKEY = "cmd+ctrl+e"

_MODIFIER_ALIASES = {
    "cmd": "cmd",
    "command": "cmd",
    "ctrl": "ctrl",
    "control": "ctrl",
    "option": "option",
    "alt": "option",
    "shift": "shift",
}

_DISPLAY_SYMBOLS = {
    "cmd": "⌘",
    "ctrl": "⌃",
    "option": "⌥",
    "shift": "⇧",
}

_MODIFIER_ORDER = ("cmd", "ctrl", "option", "shift")

_PYNPUT_MODIFIERS = {
    "cmd": (kb.Key.cmd, kb.Key.cmd_l, kb.Key.cmd_r),
    "ctrl": (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r),
    "option": (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r),
    "shift": (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r),
}


def parse_hotkey(hotkey: str) -> dict:
    parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
    modifiers = set()
    key = None
    for part in parts:
        if part in _MODIFIER_ALIASES:
            modifiers.add(_MODIFIER_ALIASES[part])
        elif len(part) == 1 and part.isalnum():
            key = part
        else:
            raise ValueError(f"Invalid hotkey part: {part}")
    if not modifiers:
        raise ValueError("Hotkey must include at least one modifier")
    if not key:
        raise ValueError("Hotkey must include a key")
    return {"modifiers": modifiers, "key": key}


def format_hotkey_display(hotkey) -> str:
    spec = parse_hotkey(hotkey) if isinstance(hotkey, str) else hotkey
    mods = "".join(_DISPLAY_SYMBOLS[m] for m in _MODIFIER_ORDER if m in spec["modifiers"])
    return f"{mods}{spec['key'].upper()}"


def format_hotkey_spoken(hotkey) -> str:
    spec = parse_hotkey(hotkey) if isinstance(hotkey, str) else hotkey
    names = {
        "cmd": "Cmd",
        "ctrl": "Control",
        "option": "Option",
        "shift": "Shift",
    }
    parts = [names[m] for m in _MODIFIER_ORDER if m in spec["modifiers"]]
    parts.append(spec["key"].upper())
    return " + ".join(parts)


def hotkey_from_nsevent_flags(key: str, flags: int) -> str:
    import AppKit

    modifiers = []
    if flags & AppKit.NSCommandKeyMask:
        modifiers.append("cmd")
    if flags & AppKit.NSControlKeyMask:
        modifiers.append("ctrl")
    if flags & AppKit.NSAlternateKeyMask:
        modifiers.append("option")
    if flags & AppKit.NSShiftKeyMask:
        modifiers.append("shift")
    if not modifiers:
        raise ValueError("Shortcut must include at least one modifier key")
    return "+".join(modifiers + [key.lower()])


def key_matches_hotkey(pressed: set, spec: dict) -> bool:
    for mod in spec["modifiers"]:
        if not any(k in pressed for k in _PYNPUT_MODIFIERS[mod]):
            return False
    key_char = spec["key"].lower()
    return any(
        hasattr(k, "char") and k.char and k.char.lower() == key_char
        for k in pressed
    )
