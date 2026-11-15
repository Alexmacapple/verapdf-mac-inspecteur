#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/opt/python@3.12/bin/python3.12}"
"$PYTHON_BIN" -c 'import pikepdf, fitz'
APP="$ROOT/build/veraPDF Mac Inspecteur.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
SWIFT_FLAGS=(-swift-version 5 -O)
if [[ "${DIAGNOSTICS:-0}" == "1" ]]; then SWIFT_FLAGS+=(-D INSPECTOR_DIAGNOSTICS); fi
xcrun swiftc "${SWIFT_FLAGS[@]}" -framework SwiftUI -framework AppKit -framework PDFKit \
    "$ROOT"/Sources/*.swift -o "$APP/Contents/MacOS/InspecteurVeraPDF"
cp "$ROOT"/worker/*.py "$APP/Contents/Resources/"
"$PYTHON_BIN" - "$APP/Contents/Info.plist" "$PYTHON_BIN" <<'PY'
import plistlib,sys,shutil
from pathlib import Path
info = dict(CFBundleIdentifier='org.alex.verapdf-inspecteur', CFBundleName='veraPDF Mac Inspecteur',
            CFBundleDisplayName='veraPDF Mac Inspecteur', CFBundleExecutable='InspecteurVeraPDF',
            CFBundlePackageType='APPL', CFBundleShortVersionString='0.2.0', CFBundleVersion='2',
            LSMinimumSystemVersion='14.0', NSHighResolutionCapable=True,
            PythonExecutable=str(Path(sys.argv[2]).absolute()))
Path(sys.argv[1]).write_bytes(plistlib.dumps(info))
cache = Path(sys.argv[1]).parent / 'Resources' / '__pycache__'
if cache.is_dir():
    shutil.rmtree(cache)
PY
codesign --force --sign - "$APP"
echo "$APP"
