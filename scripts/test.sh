#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/opt/python@3.12/bin/python3.12}"
cd "$ROOT"
"$PYTHON_BIN" -m unittest discover -s tests -v
TEST_DIR="$(mktemp -d /tmp/verapdf-tests.XXXXXX)"
trap 'rm -rf "$TEST_DIR"' EXIT
xcrun swiftc -swift-version 5 -framework SwiftUI -framework AppKit -framework PDFKit \
    Sources/PDFCanvas.swift tests/pdfcanvas/main.swift -o "$TEST_DIR/pdfcanvas"
"$TEST_DIR/pdfcanvas"
xcrun swiftc -swift-version 5 -parse-as-library -framework Combine -framework PDFKit \
    Sources/Models.swift Sources/WorkerTask.swift Sources/ReportCache.swift tests/runtime/main.swift -o "$TEST_DIR/runtime"
"$TEST_DIR/runtime" "$ROOT" "$PYTHON_BIN"
