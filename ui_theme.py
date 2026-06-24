"""Shared glassmorphism styling for VibeCode Translator UI."""

import AppKit
import Quartz
from Foundation import NSMakeRect, NSMakeSize

CORNER_RADIUS_CARD = 24
CORNER_RADIUS_FIELD = 12
CORNER_RADIUS_PILL = 18

# Pastel palette (reference: mint + peach on cream)
CREAM = (0.98, 0.97, 0.95)
MINT = (0.55, 0.85, 0.78)
MINT_SOLID = (0.45, 0.78, 0.70)
PEACH = (0.98, 0.78, 0.72)
TEXT = (0.22, 0.24, 0.28)
TEXT_SECONDARY = (0.45, 0.47, 0.50)
BORDER_ALPHA = 0.65
GLASS_FILL_ALPHA = 0.38


def rgba(rgb, alpha=1.0):
    r, g, b = rgb
    return AppKit.NSColor.colorWithRed_green_blue_alpha_(r, g, b, alpha)


def text_color(secondary=False):
    return rgba(TEXT_SECONDARY if secondary else TEXT)


def border_color():
    return rgba((1.0, 1.0, 1.0), BORDER_ALPHA)


def apply_glass_layer(view, radius=CORNER_RADIUS_CARD, masks=True):
    view.setWantsLayer_(True)
    layer = view.layer()
    layer.setCornerRadius_(radius)
    layer.setBorderWidth_(1.0)
    layer.setBorderColor_(border_color().CGColor())
    if masks:
        layer.setMasksToBounds_(True)


def make_visual_effect_view(frame, within_window=False):
    view = AppKit.NSVisualEffectView.alloc().initWithFrame_(frame)
    view.setMaterial_(AppKit.NSVisualEffectMaterialHUDWindow)
    blending = (
        AppKit.NSVisualEffectBlendingModeWithinWindow
        if within_window
        else AppKit.NSVisualEffectBlendingModeBehindWindow
    )
    view.setBlendingMode_(blending)
    view.setState_(AppKit.NSVisualEffectStateActive)
    apply_glass_layer(view)
    return view


def make_glass_card(frame, tint="mint"):
    card = make_visual_effect_view(frame, within_window=True)
    tint_rgb = MINT if tint == "mint" else PEACH
    overlay = AppKit.NSView.alloc().initWithFrame_(card.bounds())
    overlay.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
    overlay.setWantsLayer_(True)
    overlay.layer().setBackgroundColor_(rgba(tint_rgb, 0.14).CGColor())
    overlay.layer().setCornerRadius_(CORNER_RADIUS_CARD)
    card.addSubview_(overlay)
    return card


def fill_cream_background(view):
    view.setWantsLayer_(True)
    gradient = Quartz.CAGradientLayer.layer()
    gradient.setFrame_(view.bounds())
    gradient.setColors_([
        rgba(CREAM).CGColor(),
        rgba((0.96, 0.99, 0.97)).CGColor(),
        rgba((0.99, 0.96, 0.94)).CGColor(),
    ])
    gradient.setStartPoint_(Quartz.CGPoint(0, 1))
    gradient.setEndPoint_(Quartz.CGPoint(1, 0))
    view.layer().insertSublayer_atIndex_(gradient, 0)
    return gradient


def setup_glass_window(window, width, height):
    window.setContentSize_(NSMakeSize(width, height))
    window.setTitlebarAppearsTransparent_(True)
    window.setTitleVisibility_(AppKit.NSWindowTitleHidden)
    window.setStyleMask_(
        window.styleMask() | AppKit.NSWindowStyleMaskFullSizeContentView
    )
    window.setBackgroundColor_(AppKit.NSColor.clearColor())
    window.setOpaque_(False)
    window.setHasShadow_(True)
    window.setAppearance_(
        AppKit.NSAppearance.appearanceNamed_(AppKit.NSAppearanceNameAqua)
    )


def make_label(text, size=13.0, bold=False, secondary=False, centered=False):
    label = AppKit.NSTextField.labelWithString_(text)
    weight = AppKit.NSFontWeightSemibold if bold else AppKit.NSFontWeightRegular
    label.setFont_(AppKit.NSFont.systemFontOfSize_weight_(size, weight))
    label.setTextColor_(text_color(secondary))
    if centered:
        label.setAlignment_(AppKit.NSTextAlignmentCenter)
    return label


def style_text_field(field, monospace=False):
    field.setBezeled_(False)
    field.setDrawsBackground_(True)
    field.setBackgroundColor_(rgba((1.0, 1.0, 1.0), GLASS_FILL_ALPHA))
    field.setTextColor_(text_color())
    if monospace:
        field.setFont_(
            AppKit.NSFont.monospacedSystemFontOfSize_weight_(13.0, AppKit.NSFontWeightMedium)
        )
    else:
        field.setFont_(AppKit.NSFont.systemFontOfSize_(13.0))
    field.setWantsLayer_(True)
    layer = field.layer()
    layer.setCornerRadius_(CORNER_RADIUS_FIELD)
    layer.setBorderWidth_(1.0)
    layer.setBorderColor_(border_color().CGColor())


def style_popup(popup):
    popup.setBezelStyle_(AppKit.NSBezelStyleRounded)
    popup.setWantsLayer_(True)
    layer = popup.layer()
    layer.setCornerRadius_(CORNER_RADIUS_FIELD)
    layer.setBackgroundColor_(rgba((1.0, 1.0, 1.0), GLASS_FILL_ALPHA).CGColor())
    layer.setBorderWidth_(1.0)
    layer.setBorderColor_(border_color().CGColor())


def style_glass_readout(field):
    field.setEditable_(False)
    field.setSelectable_(False)
    field.setBezeled_(False)
    field.setDrawsBackground_(True)
    field.setBackgroundColor_(rgba((1.0, 1.0, 1.0), 0.5))
    field.setAlignment_(AppKit.NSTextAlignmentCenter)
    field.setFont_(
        AppKit.NSFont.monospacedSystemFontOfSize_weight_(14.0, AppKit.NSFontWeightSemibold)
    )
    field.setTextColor_(text_color())
    field.setWantsLayer_(True)
    layer = field.layer()
    layer.setCornerRadius_(CORNER_RADIUS_FIELD)
    layer.setBorderWidth_(1.0)
    layer.setBorderColor_(border_color().CGColor())


def style_pill_button(button, accent=False):
    button.setBezelStyle_(AppKit.NSBezelStyleRounded)
    button.setBordered_(False)
    button.setWantsLayer_(True)
    h = button.frame().size.height
    layer = button.layer()
    layer.setCornerRadius_(h / 2.0)
    if accent:
        layer.setBackgroundColor_(rgba(MINT_SOLID, 0.95).CGColor())
        button.setContentTintColor_(AppKit.NSColor.whiteColor())
        button.setFont_(AppKit.NSFont.systemFontOfSize_weight_(13.0, AppKit.NSFontWeightSemibold))
    else:
        layer.setBackgroundColor_(rgba((1.0, 1.0, 1.0), 0.45).CGColor())
        layer.setBorderWidth_(1.0)
        layer.setBorderColor_(border_color().CGColor())
        button.setContentTintColor_(text_color())
        button.setFont_(AppKit.NSFont.systemFontOfSize_weight_(13.0, AppKit.NSFontWeightMedium))


def style_icon_button(button):
    button.setBezelStyle_(AppKit.NSBezelStyleRounded)
    button.setBordered_(False)
    button.setWantsLayer_(True)
    layer = button.layer()
    size = button.frame().size
    layer.setCornerRadius_(min(size.width, size.height) / 2.0)
    layer.setBackgroundColor_(rgba((1.0, 1.0, 1.0), 0.42).CGColor())
    layer.setBorderWidth_(1.0)
    layer.setBorderColor_(border_color().CGColor())
    button.setContentTintColor_(text_color(secondary=True))
    button.setFont_(AppKit.NSFont.systemFontOfSize_weight_(12.0, AppKit.NSFontWeightMedium))


def configure_bubble_window(win):
    win.setOpaque_(False)
    win.setBackgroundColor_(AppKit.NSColor.clearColor())
    win.setAlphaValue_(1.0)
    win.setHasShadow_(True)
    win.setAppearance_(
        AppKit.NSAppearance.appearanceNamed_(AppKit.NSAppearanceNameAqua)
    )
