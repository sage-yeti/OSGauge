#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST="${1:-$ROOT/dist}"
APPDIR="$ROOT/AppDir"
APPIMAGE_NAME="OSGauge-Linux-x86_64.AppImage"

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp "$DIST/OSGauge-Linux-x64" "$APPDIR/usr/bin/"
cp "$ROOT/packaging/linux/AppRun" "$APPDIR/AppRun"
cp "$ROOT/packaging/linux/OS-Readiness-Checker.desktop" "$APPDIR/OS-Readiness-Checker.desktop"
cp "$ROOT/packaging/linux/OS-Readiness-Checker.svg" "$APPDIR/OS-Readiness-Checker.svg"
cp "$ROOT/packaging/linux/OS-Readiness-Checker.desktop" "$APPDIR/usr/share/applications/"
cp "$ROOT/packaging/linux/OS-Readiness-Checker.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/OSGauge-Linux-x64"

TOOL="${APPIMAGETOOL:-$ROOT/.cache/appimagetool-x86_64.AppImage}"
if [[ ! -x "$TOOL" ]]; then
  mkdir -p "$(dirname "$TOOL")"
  curl --fail --location --retry 3 \
    -o "$TOOL" \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x "$TOOL"
fi
"$TOOL" "$APPDIR" "$DIST/$APPIMAGE_NAME"
test -x "$DIST/$APPIMAGE_NAME"
printf '%s\n' "$DIST/$APPIMAGE_NAME"
