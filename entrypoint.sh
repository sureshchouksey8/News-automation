#!/bin/bash
set -eux

python news_pipeline.py "$@" || {
    echo '----- PIPELINE ERROR LOG -----'
    cat /out/run-summary.json || echo "/out/run-summary.json not found."
    exit 1
}

echo "--- Checking for /out/editorial.txt (mapped workspace) from entrypoint.sh ---"
if [ -f "/out/editorial.txt" ]; then
    echo "Found /out/editorial.txt. Content preview (first 10 lines):"
    head -n 10 "/out/editorial.txt"
else
    echo "CRITICAL: /out/editorial.txt was NOT generated or found by entrypoint.sh."
    echo "Listing contents of /out/ :"
    ls -la /out/ || echo "/out directory not accessible or empty."
fi

if [ -f "/out/run-summary.json" ]; then
    echo "--- Found /out/run-summary.json. Content: ---"
    cat "/out/run-summary.json"
else
    echo "No /out/run-summary.json found by entrypoint.sh in /out."
fi
