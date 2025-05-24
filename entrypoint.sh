#!/usr/bin/env bash
python news_pipeline.py
# Print editorial if it exists (shows in Actions log)
[ -f editorial.txt ] && cat editorial.txt
