#!/bin/bash
set -eux
python news_pipeline.py "$@" || { echo '----- PIPELINE ERROR LOG -----'; cat run-summary.json || true; exit 1; }
[ -f editorial.txt ] && cat editorial.txt || echo "No editorial.txt generated"
[ -f run-summary.json ] && cat run-summary.json || echo "No run-summary.json generated"
