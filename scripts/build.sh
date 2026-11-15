#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
source "$ROOT/scripts/environment.sh"
"$PYTHON_BIN" -c 'import pikepdf, fitz'
APP="$ROOT/build/veraPDF Mac Inspecteur.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
SWIFT_FLAGS=(-swift-version 5 -O -target "$SWIFT_TARGET")
if [[ "${DIAGNOSTICS:-0}" == "1" ]]; then SWIFT_FLAGS+=(-D INSPECTOR_DIAGNOSTICS); fi
xcrun swiftc "${SWIFT_FLAGS[@]}" -framework SwiftUI -framework AppKit -framework PDFKit \
    "$ROOT"/Sources/*.swift -o "$APP/Contents/MacOS/InspecteurVeraPDF"
cp "$ROOT"/worker/*.py "$APP/Contents/Resources/"
"$PYTHON_BIN" - "$APP/Contents/Info.plist" "$PYTHON_BIN" "$DEPLOYMENT_TARGET" <<'PY'
import plistlib,sys,shutil,subprocess,re
from pathlib import Path
info = dict(CFBundleIdentifier='org.alex.verapdf-inspecteur', CFBundleName='veraPDF Mac Inspecteur',
            CFBundleDisplayName='veraPDF Mac Inspecteur', CFBundleExecutable='InspecteurVeraPDF',
            CFBundlePackageType='APPL', CFBundleShortVersionString='0.2.1', CFBundleVersion='3',
            LSMinimumSystemVersion=sys.argv[3], NSHighResolutionCapable=True,
            PythonExecutable=str(Path(sys.argv[2]).absolute()))
Path(sys.argv[1]).write_bytes(plistlib.dumps(info))
binary = Path(sys.argv[1]).parent / 'MacOS' / info['CFBundleExecutable']
load = subprocess.run(['otool', '-l', str(binary)], capture_output=True, text=True, check=True).stdout
minimum = re.search(r'^\s*minos\s+(\S+)', load, re.M)
version = lambda value: tuple(int(part) for part in value.split('.')[:2])
if minimum is None or version(minimum[1]) != version(info['LSMinimumSystemVersion']):
    raise SystemExit('La cible du binaire et le minimum du paquet ne correspondent pas.')
cache = Path(sys.argv[1]).parent / 'Resources' / '__pycache__'
if cache.is_dir():
    shutil.rmtree(cache)
PY
codesign --force --sign - "$APP"
echo "$APP"
