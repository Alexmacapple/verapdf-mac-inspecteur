#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
source "$ROOT/scripts/environment.sh"
cd "$ROOT"
"$PYTHON_BIN" -m unittest discover -s tests -v
TEST_DIR="$(mktemp -d /tmp/verapdf-tests.XXXXXX)"
trap 'rm -rf "$TEST_DIR"' EXIT
xcrun swiftc -swift-version 5 -target "$SWIFT_TARGET" -framework SwiftUI -framework AppKit -framework PDFKit \
    Sources/PDFCanvas.swift tests/pdfcanvas/main.swift -o "$TEST_DIR/pdfcanvas"
"$TEST_DIR/pdfcanvas"
xcrun swiftc -swift-version 5 -target "$SWIFT_TARGET" -parse-as-library -framework Combine -framework PDFKit \
    Sources/Models.swift Sources/WorkerTask.swift Sources/ReportCache.swift tests/runtime/main.swift -o "$TEST_DIR/runtime"
"$TEST_DIR/runtime" "$ROOT" "$PYTHON_BIN"
sed '/^@main/,$d' Sources/App.swift > "$TEST_DIR/FileActions.swift"
xcrun swiftc -swift-version 5 -target "$SWIFT_TARGET" -parse-as-library -framework SwiftUI -framework AppKit -framework PDFKit \
    Sources/Models.swift Sources/WorkerTask.swift Sources/ReportCache.swift Sources/PDFCanvas.swift Sources/Views.swift \
    "$TEST_DIR/FileActions.swift" tests/actions/main.swift -o "$TEST_DIR/actions"
"$TEST_DIR/actions"
