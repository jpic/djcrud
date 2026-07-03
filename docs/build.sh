#!/usr/bin/env bash
# Build Sphinx HTML docs. Pass --force to regenerate committed screenshots first.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="$ROOT/docs"
FORCE=false

for arg in "$@"; do
    case "$arg" in
        --force)
            FORCE=true
            ;;
        -h|--help)
            cat <<'EOF'
Usage: docs/build.sh [--force]

Build Sphinx HTML documentation into docs/_build/html/.

  --force   Regenerate PNGs in docs/_static/screenshots/ before building
            (runs Splinter browser tests; requires Firefox/geckodriver).
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $arg (try --help)" >&2
            exit 1
            ;;
    esac
done

cd "$ROOT"

if [[ "$FORCE" == true ]]; then
    echo "Regenerating doc screenshots..."
    python -m pytest \
        tests/test_docs_screenshots.py \
        tests/test_djcrud_dal_topbar_splinter.py::test_site_search_navigates_to_user_detail \
        -n0 --splinter-headless --force
fi

echo "Building Sphinx HTML..."
make -C "$DOCS_DIR" html

echo "Done: $DOCS_DIR/_build/html/index.html"