#!/usr/bin/env bash
# Pass all CLI args ($@) into news_pipeline.py
python news_pipeline.py "$@"
# If an editorial was written, print it to the log
[ -f editorial.txt ] && cat editorial.txt
