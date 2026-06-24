"""Build VibeCode Translator as a standalone macOS .app (py2app)."""

from setuptools import setup

APP = ["main.py"]
APP_NAME = "VibeCode Translator"

OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": "com.vibecode.translator",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    },
    "packages": [
        "rumps",
        "anthropic",
        "openai",
        "pynput",
        "httpx",
        "httpcore",
        "pydantic",
        "anyio",
        "certifi",
        "idna",
        "sniffio",
        "h11",
        "jiter",
        "distro",
        "typing_extensions",
        "annotated_types",
        "pydantic_core",
    ],
    "includes": [
        "settings",
        "explainer",
        "bubble",
        "providers",
        "objc",
        "AppKit",
        "Foundation",
        "Quartz",
        "ApplicationServices",
        "CoreFoundation",
    ],
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=[],
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
