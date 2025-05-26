#!/usr/bin/env bash
set -eux
python news_pipeline.py "$@"
[ -f editorial.txt ] && cat editorial.txt
