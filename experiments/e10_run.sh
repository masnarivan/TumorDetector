#!/bin/sh
# E10: rerun E6 (empty recipe, three seeds in parallel) saving the inner LOCO logits, then the conformal analysis.
# Resumable: if the rerun's predictions exist, training is skipped.
set -e
out="data/reports/experiments/e10/e6"
if [ -f "$out/predictions.csv" ]; then
  echo "$(date '+%F %T') E6 rerun: done, skipped"
else
  echo "$(date '+%F %T') E6 rerun: start"
  uv run td task=train_head mil.register=false "mil.report_dir=$out"
  echo "$(date '+%F %T') E6 rerun: end"
fi
uv run python experiments/e10_conformal.py
