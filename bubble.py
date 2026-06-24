import threading
import AppKit
import objc
from Foundation import NSObject, NSMakeRect, NSOperationQueue

from ui_theme import (
    configure_bubble_window,
    make_glass_card,
    make_label,
    style_icon_button,
    text_color,
)

_bubble_window = None
_bubble_lock = threading.Lock()
_close_delegates = {}  # keep CloseDelegate alive: window_id → delegate

class _CloseDelegate(NSObject):
    def closeWindow_(self, sender):
        win = self._win
        win.close()
        _close_delegates.pop(id(win), None)

def show_bubble(text: str):
    def _show():
        global _bubble_window
        with _bubble_lock:
            if _bubble_window:
                _bubble_window.close()
                _bubble_window = None

            loc = AppKit.NSEvent.mouseLocation()
            width = 400
            height = 280

            screen = AppKit.NSScreen.mainScreen().frame()
            bx = min(loc.x + 16, screen.size.width - width - 10)
            by = min(loc.y + 16, screen.size.height - height - 10)
            by = max(by, 10)

            rect = NSMakeRect(bx, by, width, height)

            win = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                rect,
                AppKit.NSWindowStyleMaskBorderless | AppKit.NSWindowStyleMaskNonactivatingPanel,
                AppKit.NSBackingStoreBuffered,
                False,
            )
            configure_bubble_window(win)
            win.setLevel_(AppKit.NSFloatingWindowLevel + 1)
            win.setMovableByWindowBackground_(True)
            win.setHidesOnDeactivate_(False)

            glass = make_glass_card(NSMakeRect(0, 0, width, height), tint="mint")
            glass.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
            win.setContentView_(glass)
            content = glass

            header = make_label("✦ VibeCode Translator", size=12.0, bold=True)
            header.setFrame_(NSMakeRect(18, height - 36, 240, 18))
            content.addSubview_(header)

            close_delegate = _CloseDelegate.alloc().init()
            close_delegate._win = win
            _close_delegates[id(win)] = close_delegate

            close_btn = AppKit.NSButton.alloc().initWithFrame_(
                NSMakeRect(width - 40, height - 38, 26, 26)
            )
            close_btn.setTitle_("✕")
            style_icon_button(close_btn)
            close_btn.setTarget_(close_delegate)
            close_btn.setAction_(objc.selector(
                close_delegate.closeWindow_, signature=b"v@:@"
            ))
            content.addSubview_(close_btn)

            scroll_h = height - 58
            scroll = AppKit.NSScrollView.alloc().initWithFrame_(
                NSMakeRect(16, 14, width - 32, scroll_h)
            )
            scroll.setHasVerticalScroller_(True)
            scroll.setAutohidesScrollers_(True)
            scroll.setBorderType_(AppKit.NSNoBorder)
            scroll.setDrawsBackground_(False)

            text_view = AppKit.NSTextView.alloc().initWithFrame_(
                NSMakeRect(0, 0, width - 32, scroll_h)
            )
            text_view.setString_(text)
            text_view.setEditable_(False)
            text_view.setSelectable_(True)
            text_view.setDrawsBackground_(False)
            text_view.setTextColor_(text_color())
            text_view.setFont_(AppKit.NSFont.systemFontOfSize_(13.5))
            text_view.setTextContainerInset_(AppKit.NSMakeSize(6, 8))

            scroll.setDocumentView_(text_view)
            text_view.sizeToFit()
            content.addSubview_(scroll)

            win.makeKeyAndOrderFront_(None)
            _bubble_window = win

    NSOperationQueue.mainQueue().addOperationWithBlock_(_show)

