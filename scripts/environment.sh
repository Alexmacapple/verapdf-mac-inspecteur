# Résolution commune des exécutables et de la cible, fichier destiné à être sourcé.
PYTHON_BIN="$(command -v "${PYTHON_BIN:-/opt/homebrew/opt/python@3.12/bin/python3.12}")" || {
    echo 'Python est introuvable : fournir PYTHON_BIN ou installer Python 3.12.' >&2
    return 1
}
PYTHON_BIN="$("$PYTHON_BIN" -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$PYTHON_BIN")"
DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-14.0}"
if [[ ! "$DEPLOYMENT_TARGET" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
    echo 'MACOSX_DEPLOYMENT_TARGET doit être une version telle que 14.0.' >&2
    return 1
fi
SWIFT_TARGET="$(uname -m)-apple-macosx${DEPLOYMENT_TARGET}"
export MACOSX_DEPLOYMENT_TARGET="$DEPLOYMENT_TARGET"
