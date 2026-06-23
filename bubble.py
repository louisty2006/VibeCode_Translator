import threading
import AppKit
import objc
from Foundation import NSObject, NSMakeRect, NSTimer, NSOperationQueue
import Quartz

def _run_on_main(fn):
    """Schedule fn() on the AppKit main thread (safe to call from any thread)."""
    NSOperationQueue.mainQueue().addOperationWithBlock_(fn)

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
            width = 360
            height = 240

            # macOS origin is bottom-left; place bubble to the right and above cursor
            screen = AppKit.NSScreen.mainScreen().frame()
            bx = min(loc.x + 16, screen.size.width - width - 10)
            by = min(loc.y + 16, screen.size.height - height - 10)
            by = max(by, 10)

            rect = NSMakeRect(bx, by, width, height)

            win = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                rect,
                AppKit.NSWindowStyleMaskBorderless | AppKit.NSWindowStyleMaskNonactivatingPanel,
                AppKit.NSBackingStoreBuffered,
                False
            )
            win.setLevel_(AppKit.NSFloatingWindowLevel + 1)
            win.setOpaque_(False)
            win.setAlphaValue_(0.95)
            win.setHasShadow_(True)
            win.setMovableByWindowBackground_(True)
            win.setHidesOnDeactivate_(False)

            # Container view with rounded corners
            content = win.contentView()
            content.setWantsLayer_(True)
            content.layer().setCornerRadius_(12)
            content.layer().setBackgroundColor_(
                AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.12, 0.14, 1.0).CGColor()
            )

            # Scroll view for long text
            scroll = AppKit.NSScrollView.alloc().initWithFrame_(
                NSMakeRect(12, 12, width - 24, height - 44)
            )
            scroll.setHasVerticalScroller_(True)
            scroll.setAutohidesScrollers_(True)
            scroll.setBorderType_(AppKit.NSNoBorder)
            scroll.setDrawsBackground_(False)

            text_view = AppKit.NSTextView.alloc().initWithFrame_(
                NSMakeRect(0, 0, width - 24, height - 44)
            )
            text_view.setString_(text)
            text_view.setEditable_(False)
            text_view.setSelectable_(True)
            text_view.setDrawsBackground_(False)
            text_view.setTextColor_(AppKit.NSColor.whiteColor())
            text_view.setFont_(AppKit.NSFont.systemFontOfSize_(13.0))
            text_view.setTextContainerInset_(AppKit.NSMakeSize(4, 4))

            scroll.setDocumentView_(text_view)
            text_view.sizeToFit()
            content.addSubview_(scroll)

            close_delegate = _CloseDelegate.alloc().init()
            close_delegate._win = win
            _close_delegates[id(win)] = close_delegate

            close_btn = AppKit.NSButton.alloc().initWithFrame_(
                NSMakeRect(width - 36, height - 32, 24, 20)
            )
            close_btn.setTitle_("✕")
            close_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
            close_btn.setBordered_(False)
            close_btn.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
            close_btn.setTarget_(close_delegate)
            close_btn.setAction_(objc.selector(
                close_delegate.closeWindow_, signature=b'v@:@'
            ))
            content.addSubview_(close_btn)

            # Header label
            header = AppKit.NSTextField.alloc().initWithFrame_(
                NSMakeRect(12, height - 30, 200, 20)
            )
            header.setStringValue_("✦ VibeCode Translator")
            header.setEditable_(False)
            header.setBezeled_(False)
            header.setDrawsBackground_(False)
            header.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.6, 0.8, 1.0, 1.0))
            header.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.0))
            content.addSubview_(header)

            win.makeKeyAndOrderFront_(None)
            _bubble_window = win

            from Foundation import NSNotificationCenter
            def _on_close(note):
                import traceback
                print("[DEBUG] bubble window closed! Stack:", flush=True)
                traceback.print_stack()
            NSNotificationCenter.defaultCenter().addObserverForName_object_queue_usingBlock_(
                AppKit.NSWindowWillCloseNotification,
                win,
                NSOperationQueue.mainQueue(),
                _on_close,
            )

    NSOperationQueue.mainQueue().addOperationWithBlock_(_show)

def show_loading_bubble():
    show_bubble("⏳ Analyzing, please wait...")

def close_bubble():
    def _do_close():
        global _bubble_window
        with _bubble_lock:
            if _bubble_window:
                _bubble_window.close()
                _bubble_window = None
    _run_on_main(_do_close)
