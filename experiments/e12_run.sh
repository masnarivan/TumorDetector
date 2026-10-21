#!/bin/sh
# E12: rerun E6 (empty recipe, three seeds in parallel) saving the top instance logits, then the tile-score analysis.
# Resumable: if the rerun's instances exist, training is skipped.
set -e
out="data/reports/experiments/e12/e6"
if [ -f "$out/instances.csv" ]; then
  echo "$(date '+%F %T') E6 rerun: done, skipped"
else
  echo "$(date '+%F %T') E6 rerun: start"
  uv run td task=train_head mil.register=false "mil.report_dir=$out"
  echo "$(date '+%F %T') E6 rerun: end"
fi
uv run python experiments/e12_tile_score.py
