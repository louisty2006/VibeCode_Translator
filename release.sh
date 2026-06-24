#!/bin/bash
# Build .app, zip, and publish to GitHub Releases.
# Usage: ./release.sh X.Y.Z --notes RELEASE_NOTES_X.Y.Z.md
set -euo pipefail

cd "$(dirname "$0")"

VERSION=""
NOTES_FILE=""

usage() {
  echo "Usage: $0 X.Y.Z --notes RELEASE_NOTES.md"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --notes)
      NOTES_FILE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      if [[ -z "$VERSION" ]]; then
        VERSION="$1"
        shift
      else
        echo "Unknown argument: $1"
        usage
      fi
      ;;
  esac
done

[[ -n "$VERSION" ]] || usage
[[ -n "$NOTES_FILE" ]] || usage
[[ -f "$NOTES_FILE" ]] || { echo "Notes file not found: $NOTES_FILE"; exit 1; }

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Error: release.sh must run on macOS (py2app build)."
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI not found. Install: brew install gh && gh auth login"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: gh not authenticated. Run: gh auth login"
  exit 1
fi

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: version must be X.Y.Z (got: $VERSION)"
  exit 1
fi

TAG="v${VERSION}"
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Error: git tag $TAG already exists."
  exit 1
fi

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "Error: GitHub release $TAG already exists."
  exit 1
fi

echo "→ Updating setup.py version to $VERSION..."
sed -i '' \
  -e "s/\"CFBundleShortVersionString\": \"[^\"]*\"/\"CFBundleShortVersionString\": \"$VERSION\"/" \
  -e "s/\"CFBundleVersion\": \"[^\"]*\"/\"CFBundleVersion\": \"$VERSION\"/" \
  setup.py

echo "→ Building .app..."
./build_app.sh

APP_PATH="dist/VibeCode Translator.app"
ZIP_NAME="VibeCode-Translator-${VERSION}-macOS-arm64.zip"
ZIP_PATH="dist/${ZIP_NAME}"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Error: build output missing: $APP_PATH"
  exit 1
fi

echo "→ Creating $ZIP_NAME..."
rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo "→ Creating GitHub release $TAG..."
gh release create "$TAG" "$ZIP_PATH" \
  --title "VibeCode Translator $VERSION" \
  --notes-file "$NOTES_FILE"

echo ""
echo "✅ Release published: $TAG"
echo "   Zip: $ZIP_PATH"
gh release view "$TAG" --json url -q .url
